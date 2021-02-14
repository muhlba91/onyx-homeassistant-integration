"""Test for the ONYX API Connector."""

from unittest.mock import patch

import pytest
from onyx_client.data.device_command import DeviceCommand
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType
from onyx_client.group.group import Group

from custom_components.hella_onyx import (
    APIConnector,
)
from custom_components.hella_onyx.api_connector import (
    CommandException,
    UnknownStateException,
)


class TestAPIConnector:
    @pytest.fixture
    def api(self):
        yield APIConnector(None, "finger", "token")

    @pytest.mark.asyncio
    async def test_update(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            await api.update()
            assert len(api.devices) == 1
            assert len(api.groups) == 1
            assert mock_client.called

    def test_device(self, api):
        api.devices = {"uuid": "device"}
        assert api.device("uuid") == "device"

    def test_device_not_found(self, api):
        with pytest.raises(UnknownStateException):
            api.device("uuid")

    @pytest.mark.asyncio
    async def test_update_device(self, api):
        assert len(api.devices) == 0
        with patch.object(api, "_client", new=MockClient) as mock_client:
            await api.update_device("id")
            assert len(api.devices) == 1
            assert mock_client.called

    @pytest.mark.asyncio
    async def test_send_device_command_action(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            await api.send_device_command_action("id", Action.STOP)
            assert mock_client.called

    @pytest.mark.asyncio
    async def test_send_device_command_action_failed(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            with pytest.raises(CommandException):
                await api.send_device_command_action("id", Action.CLOSE)
            assert mock_client.called

    @pytest.mark.asyncio
    async def test_send_device_command_properties(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            await api.send_device_command_properties("id", {"action": 0})
            assert mock_client.called

    @pytest.mark.asyncio
    async def test_send_device_command_properties_failed(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            with pytest.raises(CommandException):
                await api.send_device_command_properties("id", {"fail": 0})
            assert mock_client.called

    @pytest.mark.asyncio
    async def test_listen_events(self, api):
        with patch.object(api, "_client", new=MockClient) as mock_client:
            async for device in api.listen_events():
                assert device is not None
            assert mock_client.called


class MockClient:
    def __init__(self, *kwargs):
        self.called = False

    def called(self):
        return self.called

    async def devices(self, include_details: bool):
        assert include_details
        self.called = True
        return [
            Shutter(
                "id",
                "name",
                DeviceType.RAFFSTORE_90,
                DeviceMode(DeviceType.RAFFSTORE_90),
                list(Action),
            )
        ]

    async def groups(self):
        self.called = True
        return [Group("group", "group", [])]

    async def device(self, uuid: str):
        self.called = True
        return Shutter(
            "id",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

    async def send_command(self, uuid: str, command: DeviceCommand):
        self.called = True
        return command.action == Action.STOP or (
            command.properties is not None and "fail" not in command.properties
        )

    async def events(self):
        yield Shutter(
            "id",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )
