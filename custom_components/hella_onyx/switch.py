"""The ONYX automation switches."""

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import OnyxConfigEntry
from .sensors.automation import OnyxAutomationSwitch

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the ONYX switch platform."""
    api = entry.runtime_data.api

    switches = [
        OnyxAutomationSwitch(api, automation.identifier)
        for automation in api.automations
    ]
    _LOGGER.info("adding %s hella_onyx switch entities", len(switches))
    async_add_entities(switches)
