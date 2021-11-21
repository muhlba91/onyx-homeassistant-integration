"""Test for the LED-Pi Sensor Entities."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import (
    DOMAIN,
    ONYX_API,
    ONYX_COORDINATOR,
    ONYX_TIMEZONE,
)
from custom_components.hella_onyx.sensor import (
    OnyxSensorDeviceType,
    async_setup_entry,
)


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass):
    config_entry = ConfigEntry(1, DOMAIN, "entry", {}, "source", "POLL", {})

    class AsyncAddEntries:
        def __init__(self):
            self.called_async_add_entities = False

        def call(self, sensors, boolean):
            self.called_async_add_entities = True

    async_add_entries = AsyncAddEntries()

    mock_hass.data.return_value = {
        DOMAIN: {
            "entry_id": {ONYX_API: None, ONYX_COORDINATOR: None, ONYX_TIMEZONE: "UTC"}
        }
    }

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities


class TestOnyxSensorDeviceType:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def coordinator(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Shutter(
            "id",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

    @pytest.fixture
    def entity(self, api, coordinator):
        yield OnyxSensorDeviceType(
            api, "UTC", coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:cellphone-link"

    def test_name(self, entity):
        assert entity.name == "name Device Type"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/DeviceType"

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == DeviceType.RAFFSTORE_90.string()
        assert api.device.called
