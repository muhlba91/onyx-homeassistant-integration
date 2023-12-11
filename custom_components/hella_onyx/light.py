"""The ONYX light entity."""
import logging
from typing import Callable, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from custom_components.hella_onyx import DOMAIN, ONYX_TIMEZONE
from custom_components.hella_onyx.const import ONYX_API, ONYX_COORDINATOR
from custom_components.hella_onyx.sensors.light import OnyxLight

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the ONYX light platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data[ONYX_API]
    timezone = data[ONYX_TIMEZONE]
    coordinator = data[ONYX_COORDINATOR]

    lights = [
        OnyxLight(
            api, timezone, coordinator, device.name, device.device_type, device_id
        )
        for device_id, device in filter(
            lambda item: item[1].device_type is not None
            and item[1].device_type.is_light(),
            api.devices.items(),
        )
    ]
    _LOGGER.info("adding %s hella_onyx light entities", len(lights))
    async_add_entities(lights, True)
