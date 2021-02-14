"""Test for the EventThread."""

from unittest.mock import AsyncMock, patch

import pytest
from onyx_client.data.device_mode import DeviceMode
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
        yield EventThread(api, coordinator, backoff=False)

    @pytest.mark.asyncio
    async def test_update(self, thread, api, coordinator):
        await thread._update()
        assert api.called
        assert coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_invalid_device(self, thread, api, coordinator):
        api.fail_device = True
        await thread._update()
        assert api.called
        assert not coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_connection_error(self, thread, api, coordinator):
        api.fail = True
        await thread._update()
        assert api.called
        assert not coordinator.async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_update_backoff(self, thread, api, coordinator):
        async def sleep_called(backoff: int):
            assert backoff > 0
            assert backoff / 60 < MAX_BACKOFF_TIME
            thread._backoff = False

        with patch("asyncio.sleep", new=sleep_called):
            thread._backoff = True
            api.fail = True
            assert thread._backoff
            await thread._update()
            assert api.called
            assert not thread._backoff
            assert not coordinator.async_set_updated_data.called


class MockAPI:
    def __init__(self):
        self.called = False
        self.fail = False
        self.fail_device = False

    def called(self):
        return self.called

    def device(self, uuid: str):
        if self.fail_device:
            raise UnknownStateException("ERROR")
        return Shutter("uuid", "name", None, None, None)

    async def listen_events(self):
        self.called = True
        if self.fail:
            raise NotImplementedError()
        yield Shutter(
            "uuid",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )
