"""The ONYX sensors."""
import logging
from typing import Callable, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import ONYX_API, ONYX_COORDINATOR, ONYX_TIMEZONE
from .const import DOMAIN
from .onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the ONYX shutter platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data[ONYX_API]
    timezone = data[ONYX_TIMEZONE]
    coordinator = data[ONYX_COORDINATOR]

    sensors = [
        [
            OnyxSensorDeviceType(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
        ]
        for device_id, device in api.devices.items()
    ]
    sensors = [item for sublist in sensors for item in sublist]
    _LOGGER.info("adding %s hella_onyx sensor entities", len(sensors))
    async_add_entities(sensors, True)


class OnyxSensorDeviceType(OnyxEntity):
    """ONYX Device Type Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Device Type"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/DeviceType"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:cellphone-link"

    @property
    def state(self):
        """Return the current value."""
        return self._device.device_type.string()
