"""Test for the ONYX Buttons."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.device import Device
from onyx_client.device.input import Input
from onyx_client.device.light import Light
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.button import async_setup_entry
from custom_components.hella_onyx.models import OnyxData


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
            [Action.OPEN, Action.WINK],
        ),
        "light": Light(
            "light",
            "name",
            DeviceType.BASIC_LIGHT,
            DeviceMode(DeviceType.BASIC_LIGHT),
            [Action.LIGHT_ON],
        ),
        "input": Input(
            "input",
            "name",
            DeviceType.INPUT,
            DeviceMode(DeviceType.INPUT),
            [Action.WINK],
        ),
        "click": Device(
            "click",
            "name",
            DeviceType.CLICK,
            DeviceMode(DeviceType.CLICK),
            [Action.WINK],
        ),
    }
    config_entry.runtime_data = OnyxData(api=api, config=MagicMock(), timezone="UTC")
    add_entities = MagicMock()

    await async_setup_entry(mock_hass, config_entry, add_entities)
    entities = add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "shutter/Identify",
        "input/Identify",
    ]
    for entity in entities:
        assert entity.api == api
        assert entity.timezone == "UTC"
