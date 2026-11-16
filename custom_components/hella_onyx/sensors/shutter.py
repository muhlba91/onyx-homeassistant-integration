"""The ONYX shutter entity."""

import logging
from collections.abc import Callable
from datetime import timedelta
from math import ceil
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
from onyx_client.data.numeric_value import NumericValue
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector
from ..enum.moving_state import MovingState
from ..sensors.onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)

# an animation started up to this long (in s) before a command belongs to it
REQUEST_TOLERANCE = 1


class OnyxShutter(OnyxEntity, CoverEntity):
    """A shutter entity.

    Positions are computed from the reported animations at read time. A
    command sets the expected moving state until the device reports an
    animation started after it, or the moving timeout gives it up.
    """

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a shutter entity."""
        super().__init__(api, timezone, name, device_type, uuid)
        self._requested_state = MovingState.STILL
        self._requested_at = 0.0
        self._moving_timeout_unsub: Callable[[], None] | None = None

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the pending moving timeout."""
        self._cancel_moving_timeout()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._requested_state != MovingState.STILL and self._reported_movement:
            self._set_requested_state(MovingState.STILL)
        super()._handle_coordinator_update()

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:window-shutter"

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Shutter"

    @property
    def device_class(self) -> str | None:
        """Return the class of this device, from component device class."""
        return CoverDeviceClass.SHUTTER

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

        if self._type in (DeviceType.RAFFSTORE_90, DeviceType.RAFFSTORE_180):
            supported_features |= CoverEntityFeature.SET_TILT_POSITION

        return supported_features

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._actual_position
        value = self._effective_value(position)
        if value is None or not position.maximum:
            return None
        return self._clamp_percentage(100 - int(value * 100 / position.maximum))

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Return current position of cover tilt.

        None is unknown, 0 is closed, 100 is fully open.
        """
        value = self._effective_value(self._actual_angle)
        if value is None:
            return None
        return self._clamp_percentage(int(value * 100 / self._max_angle))

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._moving_state == MovingState.OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._moving_state == MovingState.CLOSING

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        position = self._actual_position
        value = self._effective_value(position)
        if value is None or not position.maximum:
            return None
        tolerance = position.maximum * self.api.config.closed_tolerance / 100
        return value >= position.maximum - tolerance

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._send_action(Action.OPEN, MovingState.OPENING)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self._send_action(Action.CLOSE, MovingState.CLOSING)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            device = self._device
            target_position = device.target_position if device else None
            target_max = (
                target_position.maximum
                if target_position and target_position.maximum
                else 100
            )
            hella_position = ceil((100 - int(kwargs[ATTR_POSITION])) * target_max / 100)
            target_angle = device.target_angle if device else None
            await self._send_properties(
                {
                    "target_position": hella_position,
                    "target_angle": target_angle.value
                    if target_angle and target_angle.value is not None
                    else 0,
                },
                self._calculate_state(
                    self._effective_value(self._actual_position), hella_position
                ),
            )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._send_action(Action.STOP, MovingState.STILL)

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        raise NotImplementedError()

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        raise NotImplementedError()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        if ATTR_TILT_POSITION in kwargs:
            hella_angle = ceil(int(kwargs[ATTR_TILT_POSITION]) * self._max_angle / 100)
            await self._send_properties(
                {"target_angle": hella_angle},
                self._calculate_state(
                    self._effective_value(self._actual_angle), hella_angle
                ),
            )

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.async_stop_cover()

    @property
    def _actual_position(self) -> NumericValue | None:
        device = self._device
        return device.actual_position if device else None

    @property
    def _actual_angle(self) -> NumericValue | None:
        device = self._device
        return device.actual_angle if device else None

    @property
    def _animated_values(self) -> list[NumericValue | None]:
        return [self._actual_position, self._actual_angle]

    def _effective_value(self, value: NumericValue | None) -> float | None:
        """The value at the current ONYX.CENTER time."""
        return value.effective_value(self.api.now()) if value else None

    @property
    def _running_animations(self) -> list:
        """The animations which are running, including the additional delay."""
        now = self.api.now() - self.api.config.additional_delay / 1000
        return [
            value.animation
            for value in self._animated_values
            if value is not None and value.is_animating(now)
        ]

    @property
    def _reported_movement(self) -> bool:
        """Whether the device reports an animation started after the command."""
        return any(
            animation.start >= self._requested_at - REQUEST_TOLERANCE
            for animation in self._running_animations
        )

    @property
    def _moving_state(self) -> MovingState:
        """The requested state, else the direction of the running animation."""
        if self._requested_state != MovingState.STILL:
            return self._requested_state
        for animation in self._running_animations:
            return self._calculate_state(
                animation.current_value, animation.value_at(animation.end_time())
            )
        return MovingState.STILL

    async def _send_action(self, action: Action, state: MovingState):
        """Send the action, expecting the given moving state."""
        await self._send(self.api.send_device_command_action(self._uuid, action), state)

    async def _send_properties(self, properties: dict, state: MovingState):
        """Send the properties, expecting the given moving state."""
        await self._send(
            self.api.send_device_command_properties(self._uuid, properties), state
        )

    async def _send(self, command, state: MovingState):
        """Show the expected moving state while sending the command."""
        self._set_requested_state(state)
        self.async_write_ha_state()
        try:
            await command
        except BaseException:
            self._set_requested_state(MovingState.STILL)
            self.async_write_ha_state()
            raise

    def _set_requested_state(self, state: MovingState):
        """Set the expected moving state until the device reports it."""
        self._requested_state = state
        self._requested_at = self.api.now()
        self._cancel_moving_timeout()
        if state != MovingState.STILL:
            self._moving_timeout_unsub = async_call_later(
                self.hass,
                timedelta(seconds=self.api.config.moving_timeout),
                self._handle_moving_timeout,
            )

    def _cancel_moving_timeout(self):
        """Cancel the pending moving timeout, if any."""
        if self._moving_timeout_unsub is not None:
            self._moving_timeout_unsub()
            self._moving_timeout_unsub = None

    @callback
    def _handle_moving_timeout(self, *args: Any):
        """Give up the expected moving state when no animation was reported."""
        self._moving_timeout_unsub = None
        _LOGGER.debug(
            "shutter %s reported no movement within %s seconds, assuming it stopped",
            self._uuid,
            self.api.config.moving_timeout,
        )
        self._requested_state = MovingState.STILL
        self.async_write_ha_state()

    @property
    def _max_angle(self) -> int:
        """Maximum angle depending on raffstore type."""
        if self._type == DeviceType.RAFFSTORE_90:
            return 90
        elif self._type == DeviceType.RAFFSTORE_180:
            return 180
        else:
            return 100

    @staticmethod
    def _clamp_percentage(value: int) -> int:
        """Clamp the value to a valid percentage."""
        return max(0, min(100, value))

    @staticmethod
    def _calculate_state(actual: float | None, new_value: float) -> MovingState:
        """Calculate the moving state; higher ONYX values are more closed."""
        if actual is None:
            return MovingState.STILL
        if new_value < actual:
            return MovingState.OPENING
        elif new_value > actual:
            return MovingState.CLOSING
        else:
            return MovingState.STILL
