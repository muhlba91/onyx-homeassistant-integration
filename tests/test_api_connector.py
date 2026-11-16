"""Test for the ONYX API Connector."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.update_coordinator import UpdateFailed
from onyx_client.client import OnyxClient
from onyx_client.data.date_information import DateInformation
from onyx_client.data.update_status import UpdateStatus
from onyx_client.enum.action import Action
from onyx_client.enum.verify_result import VerifyResult
from onyx_client.group.group import Group
from onyx_client.stream.events import (
    AutomationsChanged,
    DeviceAdded,
    DeviceChanged,
    DeviceRemoved,
    GroupsChanged,
    Pulse,
    Snapshot,
    UpdateChanged,
)
from onyx_client.utils.mapper import init_device

from custom_components.hella_onyx.api_connector import APIConnector, CommandException
from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.const import (
    DEFAULT_ADDITIONAL_DELAY,
    DEFAULT_CLOSED_TOLERANCE,
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MOVING_TIMEOUT,
)


def shutter(identifier: str, position: int = 0):
    return init_device(
        identifier,
        {
            "name": identifier,
            "type": "rollershutter",
            "properties": {"actual_position": {"value": position, "maximum": 100}},
        },
    )


def snapshot(*devices):
    return Snapshot(
        {device.identifier: device for device in devices},
        {"group": Group("group", "Group", ["a"])},
        [],
        UpdateStatus("2.13.4"),
    )


class FakeClient:
    """A client streaming the given events, then staying connected."""

    def __init__(self, events=(), error=None):
        self.events = list(events)
        self.error = error
        self.verify = AsyncMock(return_value=VerifyResult.OK)
        self.resync = MagicMock()
        self.close = AsyncMock()
        self.now = MagicMock(return_value=1.5)
        self.send_command = AsyncMock(return_value=True)
        self.date_information = AsyncMock(
            return_value=DateInformation(0, "Europe/Vienna", 0)
        )

    async def stream(self):
        for event in self.events:
            yield event
        if self.error is not None:
            raise self.error
        await asyncio.Event().wait()


class TestAPIConnector:
    @pytest.fixture
    def config(self):
        yield Configuration(
            60,
            DEFAULT_MIN_DIM_DURATION,
            DEFAULT_MAX_DIM_DURATION,
            DEFAULT_ADDITIONAL_DELAY,
            DEFAULT_INTERPOLATION_FREQUENCY,
            DEFAULT_CLOSED_TOLERANCE,
            DEFAULT_MOVING_TIMEOUT,
            "finger",
            "token",
            None,
        )

    @pytest.fixture
    def entry(self):
        entry = MagicMock()
        entry.entry_id = "entry"
        yield entry

    @pytest.fixture
    def client(self):
        yield FakeClient([snapshot(shutter("a"))])

    @pytest.fixture
    async def api(self, hass, config, entry, client):
        api = APIConnector(hass, config)
        api.config_entry = entry
        api._APIConnector__client = client
        yield api
        await api._stop_stream()

    async def test_init(self, hass, config):
        api = APIConnector(hass, config)
        assert api.name == "hella_onyx"
        assert api.config == config
        assert api.update_interval.total_seconds() == 3600
        assert api.devices == {}
        assert api.groups == {}
        assert api.data["automations"] == []
        assert api.data["update"] is None

    async def test_client(self, hass, config):
        api = APIConnector(hass, config)
        client = api._client()
        assert isinstance(client, OnyxClient)
        assert client.config.fingerprint == "finger"
        assert client.config.access_token == "token"
        assert api._client() is client

    async def test_client_arguments(self, hass, config):
        config.local_address = "10.0.0.1"
        api = APIConnector(hass, config)
        with (
            patch("custom_components.hella_onyx.api_connector.create") as create,
            patch(
                "custom_components.hella_onyx.api_connector.async_get_clientsession"
            ) as session,
        ):
            api._client()
        session.assert_called_once_with(hass)
        create.assert_called_once_with(
            fingerprint="finger",
            access_token="token",
            client_session=session.return_value,
            local_address="10.0.0.1",
        )

    async def test_first_update_waits_for_snapshot(self, api, client):
        data = await api._async_update_data()
        assert client.verify.called
        assert list(data["devices"]) == ["a"]
        assert list(data["groups"]) == ["group"]
        assert data["update"].current == "2.13.4"
        assert data["automations"] == []
        assert api.device("a").identifier == "a"
        assert api.device("unknown") is None
        assert not client.resync.called

    async def test_update_resyncs_running_stream(self, api, client):
        await api._async_update_data()
        data = await api._async_update_data()
        assert client.resync.called
        assert data is api.data
        assert client.verify.call_count == 1

    async def test_update_restarts_ended_stream(self, api, client):
        client.error = ClientResponseError(MagicMock(), (), status=500)
        await api._async_update_data()
        await asyncio.sleep(0)
        assert api._stream_task.done()
        client.error = None
        await api._async_update_data()
        assert client.verify.call_count == 2
        assert not client.resync.called

    @pytest.mark.parametrize(
        ("result", "exception"),
        [
            (VerifyResult.UNAUTHORIZED, ConfigEntryAuthFailed),
            (VerifyResult.VERSION_UNSUPPORTED, ConfigEntryError),
            (VerifyResult.UNREACHABLE, UpdateFailed),
        ],
    )
    async def test_update_verify_fails(self, api, client, result, exception):
        client.verify.return_value = result
        with pytest.raises(exception):
            await api._async_update_data()
        assert api._stream_task is None

    async def test_update_without_snapshot(self, api, client):
        client.events = []
        with (
            patch("custom_components.hella_onyx.api_connector.SNAPSHOT_TIMEOUT", 0),
            pytest.raises(UpdateFailed),
        ):
            await api._async_update_data()
        assert client.close.called
        assert api._stream_task is None
        assert api._APIConnector__client is None

    async def test_stream_fails_unexpectedly(self, api, client):
        client.error = RuntimeError("boom")
        await api._async_update_data()
        await api._stream_task
        assert api._stream_task.exception() is None

    async def test_stream_rejected_starts_reauth(self, api, client, entry):
        client.error = ClientResponseError(MagicMock(), (), status=401)
        await api._async_update_data()
        await api._stream_task
        entry.async_start_reauth.assert_called_once_with(api.hass)

    async def test_shutdown(self, api, client):
        await api._async_update_data()
        task = api._stream_task
        await api.async_shutdown()
        await asyncio.sleep(0)
        assert client.close.called
        assert task.cancelled()
        assert api._stream_task is None

    async def test_shutdown_without_client(self, hass, config):
        api = APIConnector(hass, config)
        await api.async_shutdown()
        assert api._stream_task is None

    async def test_device_changed_updates_only_its_listeners(self, api):
        api._handle_event(snapshot(shutter("a"), shutter("b")))
        listener_a = MagicMock()
        listener_b = MagicMock()
        api.async_add_listener(listener_a, "a")
        api.async_add_listener(listener_b, "b")

        device = shutter("a", 50)
        api._handle_event(DeviceChanged(device))
        assert api.device("a") is device
        assert listener_a.called
        assert not listener_b.called

    async def test_device_removed(self, api):
        api._handle_event(snapshot(shutter("a")))
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(DeviceRemoved("a"))
        api._handle_event(DeviceRemoved("unknown"))
        assert api.device("a") is None
        assert listener.call_count == 1

    async def test_snapshot_updates_all_listeners(self, api):
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(snapshot(shutter("a")))
        assert listener.called

    async def test_device_added_reloads(self, hass, api, entry):
        api._handle_event(snapshot(shutter("a")))
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            device = shutter("a")
            api._handle_event(DeviceAdded(device))
            assert not reload.called
            assert listener.called
            assert api.device("a") is device
            api._handle_event(DeviceAdded(shutter("b")))
            api._handle_event(DeviceAdded(shutter("b")))
            api._handle_event(snapshot(shutter("a"), shutter("b")))
            reload.assert_called_once_with("entry")
        assert api.device("b") is not None

    async def test_snapshot_with_new_device_reloads(self, hass, api):
        api._handle_event(snapshot(shutter("a"), shutter("b")))
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(snapshot(shutter("a")))
            assert not reload.called
            api._handle_event(snapshot(shutter("a"), shutter("c")))
            reload.assert_called_once_with("entry")

    async def test_reload_without_entry(self, hass, config):
        api = APIConnector(hass, config)
        api._handle_event(snapshot())
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(DeviceAdded(shutter("a")))
            assert not reload.called

    async def test_collections_changed(self, api):
        api._handle_event(snapshot(shutter("a")))
        groups = {"other": Group("other", "Other", [])}
        api._handle_event(GroupsChanged(groups))
        api._handle_event(AutomationsChanged(["automation"]))
        api._handle_event(UpdateChanged(UpdateStatus("2.14.0")))
        api._handle_event(Pulse(1.0))
        assert api.groups == groups
        assert api.data["automations"] == ["automation"]
        assert api.data["update"].current == "2.14.0"

    async def test_now(self, api):
        assert api.now() == 1.5

    async def test_get_timezone(self, api):
        assert await api.get_timezone() == "Europe/Vienna"

    async def test_get_timezone_fallback(self, api, client):
        client.date_information.return_value = None
        assert await api.get_timezone() == "UTC"

    async def test_send_device_command_action(self, api, client):
        await api.send_device_command_action("id", Action.STOP)
        identifier, command = client.send_command.call_args.args
        assert identifier == "id"
        assert command.action == Action.STOP

    async def test_send_device_command_properties(self, api, client):
        await api.send_device_command_properties("id", {"target_position": 1})
        identifier, command = client.send_command.call_args.args
        assert identifier == "id"
        assert command.properties == {"target_position": 1}

    async def test_send_device_command_failed(self, api, client):
        client.send_command.return_value = False
        with pytest.raises(CommandException) as ex:
            await api.send_device_command_action("id", Action.CLOSE)
        assert ex.value.uuid == "id"
        with pytest.raises(CommandException):
            await api.send_device_command_properties("id", {})
