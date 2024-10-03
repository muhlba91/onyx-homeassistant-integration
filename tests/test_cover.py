"""Test for the ONYX Shutter Entity."""

import pytest

from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntry

from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.light import Light
from onyx_client.device.shutter import Shutter
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import (
    DOMAIN,
    ONYX_API,
    ONYX_TIMEZONE,
)
from custom_components.hella_onyx.cover import async_setup_entry


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
    assert len(async_add_entries.data) == 1
    assert async_add_entries.data[0]._uuid == "shutter"


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
    api.data = {
        "devices": {
            "light": Light(
                "light",
                "name",
                DeviceType.BASIC_LIGHT,
                DeviceMode(DeviceType.BASIC_LIGHT),
                list(),
            )
        }
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
