"""Test for the ONYX Sensors."""

import pytest

from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntry

from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.device import Device
from onyx_client.device.light import Light
from onyx_client.device.weather import Weather
from onyx_client.device.shutter import Shutter
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import (
    DOMAIN,
    ONYX_API,
    ONYX_TIMEZONE,
)
from custom_components.hella_onyx.sensor import async_setup_entry


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass):
    config_entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="entry",
        data={},
        source="source",
        unique_id="onyx",
        options={},
        discovery_keys={},
    )
    api = MagicMock()
    api.devices = {
        "shutter": Shutter(
            "shutter",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(),
        ),
        "light": Light(
            "light",
            "name",
            DeviceType.BASIC_LIGHT,
            DeviceMode(DeviceType.BASIC_LIGHT),
            list(),
        ),
        "weather": Weather(
            "weather",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(),
        ),
        "none": Shutter(
            "none",
            "name",
            None,
            None,
            list(),
        ),
    }
    async_add_entries = AsyncAddEntries()
    mock_hass.data = {
        DOMAIN: {
            config_entry.entry_id: {
                ONYX_API: api,
                ONYX_TIMEZONE: "UTC",
            }
        }
    }

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities
    assert len(async_add_entries.data) == 9
    assert async_add_entries.data[0]._uuid == "shutter"
    assert async_add_entries.data[0].unique_id == "shutter/DeviceType"
    assert async_add_entries.data[1]._uuid == "light"
    assert async_add_entries.data[1].unique_id == "light/DeviceType"
    assert async_add_entries.data[2]._uuid == "weather"
    assert async_add_entries.data[2].unique_id == "weather/DeviceType"
    assert async_add_entries.data[3]._uuid == "weather"
    assert async_add_entries.data[3].unique_id == "weather/Humidity"
    assert async_add_entries.data[4]._uuid == "weather"
    assert async_add_entries.data[4].unique_id == "weather/Temperature"
    assert async_add_entries.data[5]._uuid == "weather"
    assert async_add_entries.data[5].unique_id == "weather/AirPressure"
    assert async_add_entries.data[6]._uuid == "weather"
    assert async_add_entries.data[6].unique_id == "weather/WindPeak"
    assert async_add_entries.data[7]._uuid == "weather"
    assert async_add_entries.data[7].unique_id == "weather/SunBrightnessPeak"
    assert async_add_entries.data[8]._uuid == "weather"
    assert async_add_entries.data[8].unique_id == "weather/SunBrightnessSink"


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry_filter_all(mock_hass):
    config_entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="entry",
        data={},
        source="source",
        unique_id="onyx",
        options={},
        discovery_keys={},
    )
    api = MagicMock()
    api.devices = {
        "click": Device(
            "click",
            "name",
            DeviceType.CLICK,
            DeviceMode(DeviceType.CLICK),
            list(),
        )
    }
    async_add_entries = AsyncAddEntries()
    mock_hass.data = {
        DOMAIN: {
            config_entry.entry_id: {
                ONYX_API: api,
                ONYX_TIMEZONE: "UTC",
            }
        }
    }

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities
    assert len(async_add_entries.data) == 0


class AsyncAddEntries:
    def __init__(self):
        self.called_async_add_entities = False
        self.data = list()

    def call(self, data, boolean):
        self.data = data
        self.called_async_add_entities = True
