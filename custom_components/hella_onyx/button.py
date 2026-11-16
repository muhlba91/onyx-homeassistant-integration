"""The ONYX buttons."""

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType
from onyx_client.enum.action import Action

from . import OnyxConfigEntry
from .devices import is_supported
from .sensors.identify import OnyxButtonIdentify

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the ONYX button platform."""
    api = entry.runtime_data.api
    timezone = entry.runtime_data.timezone

    buttons = [
        OnyxButtonIdentify(api, timezone, device.name, device.device_type, device_id)
        for device_id, device in filter(
            lambda item: (
                is_supported(item[1].device_type) and Action.WINK in item[1].actions
            ),
            api.devices.items(),
        )
    ]
    _LOGGER.info("adding %s hella_onyx button entities", len(buttons))
    async_add_entities(buttons)
