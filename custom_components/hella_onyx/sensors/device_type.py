"""The ONYX device type sensor."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from ..sensors.onyx_entity import OnyxEntity


class OnyxSensorDeviceType(OnyxEntity, SensorEntity):
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
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:cellphone-link"

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        device = self._device
        return device.device_type.string() if device else None


class OnyxSensorUnknownDeviceType(OnyxSensorDeviceType):
    """ONYX Device Type Sensor of a device type the integration does not support."""

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information with the reported device type as model."""
        device_info = super().device_info
        raw_type = self.native_value
        if raw_type is not None:
            device_info["model"] = raw_type
        return device_info

    @property
    def native_value(self) -> str | None:
        """Return the device type as reported by the ONYX.CENTER."""
        device = self._device
        return device.raw_type if device else None
