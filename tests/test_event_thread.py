"""Test for the EventThread."""

from unittest.mock import AsyncMock, patch

import pytest
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import (
    EventThread,
)
from custom_components.hella_onyx.api_connector import (
    UnknownStateException,
)
from custom_components.hella_onyx.const import MAX_BACKOFF_TIME


class TestEventThread:
    @pytest.fixture
    def api(self):
        yield MockAPI()

    @pytest.fixture
    def coordinator(self):
        yield AsyncMock()

    @pytest.fixture
    def thread(self, api, coordinator):
        yield EventThread(api, coordinator, force_update=False, backoff=False)

    @pytest.mark.asyncio
    async def test_update(self, thread, api, coordinator):
        api.called = False
        await thread._update()
        assert api.is_called
        assert not api.is_force_update
        assert coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_force_update(self, thread, api, coordinator):
        thread._force_update = True
        api.called = False
        await thread._update()
        assert api.is_called
        assert api.is_force_update
        assert coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_invalid_device(self, thread, api, coordinator):
        api.called = False
        api.fail_device = True
        await thread._update()
        assert api.is_called
        assert not api.is_force_update
        assert coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_none_device(self, thread, api, coordinator):
        api.called = False
        api.none_device = True
        await thread._update()
        assert api.is_called
        assert not api.is_force_update
        assert coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_connection_error(self, thread, api, coordinator):
        api.called = False
        api.fail = True
        await thread._update()
        assert api.is_called
        assert not api.is_force_update
        assert not coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_backoff(self, thread, api, coordinator):
        api.called = False

        async def sleep_called(backoff: int):
            assert backoff >= 0
            assert backoff / 60 < MAX_BACKOFF_TIME
            thread._backoff = False

        with patch("asyncio.sleep", new=sleep_called):
            thread._backoff = True
            api.fail = True
            assert thread._backoff
            await thread._update()
            assert api.is_called
            assert not api.is_force_update
            assert not thread._backoff
            assert not coordinator.async_set_updated_data.called


class MockAPI:
    def __init__(self):
        self.called = False
        self.force_update = False
        self.fail = False
        self.fail_device = False
        self.none_device = False

    @property
    def is_called(self):
        return self.called

    @property
    def is_force_update(self):
        return self.force_update

    def device(self, uuid: str):
        self.called = True
        if self.none_device:
            return None
        if self.fail_device:
            raise UnknownStateException("ERROR")
        numeric = NumericValue(10, 10, 10, False, None)
        return Shutter(
            "uuid", "name", None, None, None, None, numeric, numeric, numeric
        )

    def updated_device(self, device):
        self.called = True

    async def events(self, force_update: bool):
        self.called = True
        self.force_update = force_update
        if self.fail:
            raise NotImplementedError()
        yield Shutter(
            "uuid",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )
