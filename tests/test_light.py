"""Test for the ONYX Light Entity."""

import pytest

from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntry

from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.light import Light
from onyx_client.device.shutter import Shutter
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.models import OnyxData
from custom_components.hella_onyx.light import async_setup_entry


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
        subentries_data={},
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
    config_entry.runtime_data = OnyxData(api=api, config=MagicMock(), timezone="UTC")
    async_add_entries = AsyncAddEntries()

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities
    assert async_add_entries.update_before_add is True
    assert len(async_add_entries.data) == 1
    entity = async_add_entries.data[0]
    assert entity._uuid == "light"
    assert entity._name == "name"
    assert entity._type == DeviceType.BASIC_LIGHT
    assert entity.api == api
    assert entity.timezone == "UTC"


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
        subentries_data={},
    )
    api = MagicMock()
    api.data = {
        "devices": {
            "shutter": Shutter(
                "shutter",
                "name",
                DeviceType.RAFFSTORE_90,
                DeviceMode(DeviceType.RAFFSTORE_90),
                list(),
            )
        }
    }
    config_entry.runtime_data = OnyxData(api=api, config=MagicMock(), timezone="UTC")
    async_add_entries = AsyncAddEntries()

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities
    assert len(async_add_entries.data) == 0


class AsyncAddEntries:
    def __init__(self):
        self.called_async_add_entities = False
        self.data = list()
        self.update_before_add = None

    def call(self, data, boolean):
        self.data = data
        self.called_async_add_entities = True
        self.update_before_add = boolean
