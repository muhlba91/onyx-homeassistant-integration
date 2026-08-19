"""The ONYX shutter entity."""

import logging

from typing import Callable, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import OnyxConfigEntry
from .sensors.shutter import OnyxShutter

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the ONYX shutter platform."""
    api = entry.runtime_data.api
    timezone = entry.runtime_data.timezone

    shutters = [
        OnyxShutter(api, timezone, device.name, device.device_type, device_id)
        for device_id, device in filter(
            lambda item: (
                item[1].device_type is not None and item[1].device_type.is_shutter()
            ),
            api.devices.items(),
        )
    ]
    _LOGGER.info("adding %s hella_onyx shutter entities", len(shutters))
    async_add_entities(shutters, True)
