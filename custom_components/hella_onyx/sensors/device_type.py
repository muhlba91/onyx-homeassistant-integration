"""The ONYX device type sensor."""

from ..sensors.onyx_entity import OnyxEntity


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
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:cellphone-link"

    @property
    def state(self) -> str:
        """Return the current value."""
        return self._device.device_type.string()
