"""The ONYX shutter entity."""
import asyncio
import logging
from datetime import timedelta
from math import ceil
from typing import Any, Callable, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
    DEVICE_CLASS_SHUTTER,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import (
    track_point_in_utc_time,
)
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import utcnow
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from . import APIConnector, DOMAIN
from .const import INCREASED_INTERVAL_DELTA, ONYX_API, ONYX_COORDINATOR
from .moving_state import MovingState
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

    shutters = [
        OnyxShutter(api, coordinator, device.name, device.device_type, device_id)
        for device_id, device in api.devices.items()
    ]
    _LOGGER.info("adding %s hella_onyx entities", len(shutters))
    async_add_entities(shutters, True)


class OnyxShutter(OnyxEntity, CoverEntity):
    """A shutter entity."""

    def __init__(
        self,
        api: APIConnector,
        coordinator: DataUpdateCoordinator,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a shutter entity."""
        super().__init__(api, coordinator, name, device_type, uuid)
        self._moving_state = MovingState.STILL

    @property
    def name(self) -> str:
        """Return the display name of the light."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the light."""
        return f"{self._uuid}/Shutter"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_SHUTTER

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = (
            SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
        )

        if (
            self._type
            in (DeviceType.RAFFSTORE_90, DeviceType.RAFFSTORE_180)
            is not None
        ):
            supported_features |= SUPPORT_SET_TILT_POSITION

        return supported_features

    @property
    def current_cover_position(self) -> int:
        """Return current position of cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._device.actual_position
        return int(
            self._invert_position(position.value, position.maximum)
            / position.maximum
            * 100
        )

    @property
    def current_cover_tilt_position(self) -> int:
        """Return current position of cover tilt.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._device.actual_angle
        return int(
            self._invert_position(position.value, self._max_angle, True)
            / self._max_angle
            * 100
        )

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._moving_state == MovingState.OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._moving_state == MovingState.CLOSING

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed or not."""
        position = self._device.actual_position
        return position.value == position.maximum

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.OPEN), self.hass.loop
        )
        self._set_state(
            MovingState.OPENING,
            delta=self._device.actual_position.value,
            max_timedelta=self._device.drivetime_up.value,
        )

    def close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.CLOSE),
            self.hass.loop,
        )
        self._set_state(
            MovingState.CLOSING,
            delta=100 - self._device.actual_position.value,
            max_timedelta=self._device.drivetime_down.value,
        )

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = self._invert_position(
                int(kwargs.get(ATTR_POSITION)), self._device.target_position.maximum
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid,
                    {
                        "target_position": position,
                        "target_angle": self._device.target_angle.value,
                    },
                ),
                self.hass.loop,
            )
            self._calculate_and_set_state(
                self._device.actual_position.value, position, -1
            )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.STOP), self.hass.loop
        ).result()
        self._set_state(MovingState.STILL)

    def open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        raise NotImplementedError()

    def close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        raise NotImplementedError()

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        if ATTR_TILT_POSITION in kwargs:
            angle = int(kwargs.get(ATTR_TILT_POSITION))
            hella_angle = self._invert_position(
                ceil(angle * (self._max_angle / 100)), self._max_angle, False
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid, {"target_angle": hella_angle}
                ),
                self.hass.loop,
            )
            self._calculate_and_set_state(
                self._device.actual_angle.value,
                hella_angle,
                self._device.rotationtime.value,
            )

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.STOP), self.hass.loop
        )
        self._set_state(MovingState.STILL)

    def _set_state(self, state: MovingState, **kwargs: Any):
        """Set the new moving state."""
        self._moving_state = state
        if state != MovingState.STILL:
            delta = int(kwargs.get("delta"))
            max_timedelta = int(kwargs.get("max_timedelta"))
            needed_time = int(max_timedelta / 100 * delta)
            _LOGGER.debug("moving by %s takes %s", delta, needed_time)
            self._start_moving_device(needed_time)
        else:
            asyncio.run_coroutine_threadsafe(self.async_update(), self.hass.loop)

    def _start_moving_device(self, delta: int):
        """Start the update loop."""
        track_point_in_utc_time(
            self.hass,
            self._end_moving_device,
            utcnow() + timedelta(milliseconds=delta + INCREASED_INTERVAL_DELTA),
        )

    def _end_moving_device(self, *args: Any):
        """Call STOP to update the device values on ONYX."""
        self.stop_cover()

    def _calculate_and_set_state(self, actual: int, new_value: int, max_timedelta: int):
        """Calculate and set the new moving state."""
        new_state = self._calculate_state(actual, new_value)
        if max_timedelta == -1:
            if new_state == MovingState.CLOSING:
                max_timedelta = self._device.drivetime_down.value
            elif new_state == MovingState.OPENING:
                max_timedelta = self._device.drivetime_up.value
        self._set_state(
            new_state,
            delta=abs(actual - new_value),
            max_timedelta=max_timedelta,
        )

    @property
    def _max_angle(self) -> int:
        """Maximum angle depending on raffstore type."""
        if self._type == DeviceType.RAFFSTORE_90:
            return 90
        elif self._type == DeviceType.RAFFSTORE_180:
            return 180
        else:
            return 100

    def _calculate_state(self, actual: int, new_value: int) -> MovingState:
        """Calculate the new moving state."""
        if new_value < actual:
            return (
                MovingState.CLOSING
                if not self._device.switch_drive_direction.value
                else MovingState.OPENING
            )
        elif new_value > actual:
            return (
                MovingState.OPENING
                if not self._device.switch_drive_direction.value
                else MovingState.CLOSING
            )
        else:
            return MovingState.STILL

    def _invert_position(self, value: int, maximum: int, invert: bool = True) -> int:
        """Inverts the position based on the drive direction."""
        if self._device.switch_drive_direction.value and invert:
            return value
        return maximum - value
