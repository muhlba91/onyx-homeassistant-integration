"""The ONYX system state sensor."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from onyx_client.data.enum_value import EnumValue

from ..sensors.onyx_entity import OnyxEntity


class OnyxSensorSystemState(OnyxEntity, SensorEntity):
    """ONYX System State Sensor (calibration and collision state of a shutter)."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} System State"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/SystemState"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:alert-circle-check-outline"

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    @property
    def device_class(self) -> str | None:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.ENUM

    @property
    def options(self) -> list[str] | None:
        """Return the possible states, including an undocumented current one."""
        system_state = self._system_state
        if system_state is None:
            return None
        options = list(system_state.values)
        if system_state.value is not None and system_state.value not in options:
            options.append(system_state.value)
        return options

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        system_state = self._system_state
        return system_state.value if system_state else None

    @property
    def _system_state(self) -> EnumValue | None:
        """Return the system state property of the device, if any."""
        return getattr(self._device, "system_state", None)
