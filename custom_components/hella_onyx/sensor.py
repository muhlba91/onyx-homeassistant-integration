"""The ONYX sensors."""
import logging
from typing import Callable, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TIME_MILLISECONDS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from . import ONYX_API, ONYX_COORDINATOR
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
    coordinator = data[ONYX_COORDINATOR]

    sensors = [
        [
            OnyxSensorDeviceType(
                api, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorSwitchDriveDirection(
                api, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorDriveTimeUp(
                api, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorDriveTimeDown(
                api, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorRotationTime(
                api, coordinator, device.name, device.device_type, device_id
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


class OnyxSensorSwitchDriveDirection(OnyxEntity):
    """ONYX Switch Drive Type Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Switch Drive Direction"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/SwitchDriveDirection"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:directions-fork"

    @property
    def state(self):
        """Return the current value."""
        return self._device.switch_drive_direction.value


class OnyxSensorDriveTimeUp(OnyxEntity):
    """ONYX Drive Time Up Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Drive Time Up"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/DriveTimeUp"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:arrow-up"

    @property
    def state(self):
        """Return the current value."""
        return self._device.drivetime_up.value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TIME_MILLISECONDS


class OnyxSensorDriveTimeDown(OnyxEntity):
    """ONYX Drive Time Down Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Drive Time Down"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/DriveTimeDown"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:arrow-down"

    @property
    def state(self):
        """Return the current value."""
        return self._device.drivetime_down.value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TIME_MILLISECONDS


class OnyxSensorRotationTime(OnyxEntity):
    """ONYX Rotation Time Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Rotation Time"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/RotationTime"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:rotate-3d-variant"

    @property
    def state(self):
        """Return the current value."""
        return self._device.rotationtime.value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TIME_MILLISECONDS
