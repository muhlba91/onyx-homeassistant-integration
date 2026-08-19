"""The ONYX light entity."""

import logging

from typing import Callable, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import OnyxConfigEntry
from .sensors.light import OnyxLight

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the ONYX light platform."""
    api = entry.runtime_data.api
    timezone = entry.runtime_data.timezone

    lights = [
        OnyxLight(api, timezone, device.name, device.device_type, device_id)
        for device_id, device in filter(
            lambda item: (
                item[1].device_type is not None and item[1].device_type.is_light()
            ),
            api.devices.items(),
        )
    ]
    _LOGGER.info("adding %s hella_onyx light entities", len(lights))
    async_add_entities(lights, True)
