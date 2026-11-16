"""The ONYX active command sensor."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.util import dt as dt_util

from ..sensors.onyx_entity import OnyxEntity

# the state when the device executes no command
NO_COMMAND = "none"
# the state when the ONYX.CENTER cannot attribute the command
UNATTRIBUTED = "unattributed"


class OnyxSensorActiveCommand(OnyxEntity, SensorEntity):
    """ONYX Active Command Sensor.

    The state is the type of the command's source; the details are attributes,
    which are excluded from the recorder as they change with every command.
    """

    _unrecorded_attributes = frozenset(
        {
            "source_name",
            "source_id",
            "action",
            "properties",
            "attributes",
            "active_indicators",
            "valid_from",
            "best_before",
        }
    )

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Active Command"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/ActiveCommand"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:console"

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        """Return the source type of the active command."""
        device = self._device
        if device is None:
            return None
        command = device.active_command
        if command is None:
            return NO_COMMAND
        if command.source is None or command.source.source_type is None:
            return UNATTRIBUTED
        return command.source.source_type

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the details of the active command."""
        device = self._device
        command = device.active_command if device else None
        if command is None:
            return None
        source = command.source
        return {
            "source_name": source.name if source else None,
            "source_id": source.identifier if source else None,
            "action": command.action.string() if command.action else None,
            "properties": command.properties,
            "attributes": [
                attribute.string()
                for attribute in command.attributes
                if attribute is not None
            ],
            "active_indicators": command.active_indicators,
            "valid_from": _timestamp(command.valid_from),
            "best_before": _timestamp(command.best_before),
        }


def _timestamp(value: int | None) -> str | None:
    """Convert an ONYX.CENTER timestamp to an ISO 8601 string, if known."""
    if value is None:
        return None
    try:
        return dt_util.utc_from_timestamp(value).isoformat()
    except (OverflowError, OSError, TypeError, ValueError):
        return None
