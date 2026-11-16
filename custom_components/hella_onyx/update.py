"""The ONYX update entity."""

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import OnyxConfigEntry
from .sensors.update import OnyxUpdate

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the ONYX update platform."""
    _LOGGER.info("adding the hella_onyx update entity")
    async_add_entities([OnyxUpdate(entry.runtime_data.api)])
