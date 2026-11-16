"""The ONYX input binary sensor."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from ..sensors.onyx_entity import OnyxEntity

# the device class by the configured role of the contact
DEVICE_CLASSES = {
    "rain_sensor": BinarySensorDeviceClass.MOISTURE,
    "fire_alarm": BinarySensorDeviceClass.SMOKE,
    "wind_alarm": BinarySensorDeviceClass.SAFETY,
    "generic_alarm": BinarySensorDeviceClass.SAFETY,
}


class OnyxBinarySensorInput(OnyxEntity, BinarySensorEntity):
    """ONYX Input Binary Sensor (a wired rain sensor or alarm contact)."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Input"

    @property
    def icon(self) -> str | None:
        """Icon to use in the frontend, if any (the icon of the device class)."""
        return None

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of the configured role of the contact."""
        input_type = getattr(self._device, "input_type", None)
        return DEVICE_CLASSES.get(input_type.value) if input_type else None

    @property
    def is_on(self) -> bool | None:
        """Return whether the contact is triggered."""
        input_active = getattr(self._device, "input_active", None)
        return input_active.as_bool() if input_active else None
