"""The ONYX binary sensors."""

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import OnyxConfigEntry
from .sensors.input import OnyxBinarySensorInput

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the ONYX binary sensor platform."""
    api = entry.runtime_data.api
    timezone = entry.runtime_data.timezone

    sensors = [
        OnyxBinarySensorInput(api, timezone, device.name, device.device_type, device_id)
        for device_id, device in filter(
            lambda item: item[1].device_type.is_input(),
            api.devices.items(),
        )
    ]
    _LOGGER.info("adding %s hella_onyx binary sensor entities", len(sensors))
    async_add_entities(sensors)
