"""The ONYX shutter entity."""
import asyncio
import logging
import time

from datetime import timedelta
from math import ceil
from typing import Any, Optional

from homeassistant.core import callback
from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
)
from homeassistant.util import utcnow

from onyx_client.data.animation_value import AnimationValue
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector
from ..const import INCREASED_INTERVAL_DELTA
from ..enum.moving_state import MovingState
from ..sensors.onyx_entity import OnyxEntity
from ..util.interpolation import interpolate

_LOGGER = logging.getLogger(__name__)


class OnyxShutter(OnyxEntity, CoverEntity):
    """A shutter entity."""

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
        self._moving_state = MovingState.STILL

    @callback
    def _handle_coordinator_update(self) -> None:
        position_animation = self._device.actual_position.animation
        if position_animation is not None and len(position_animation.keyframes) > 0:
            _LOGGER.debug(
                "received position_animation for shutter %s: %s",
                self._uuid,
                position_animation,
            )
            self._start_moving_device(position_animation)

        angle_animation = self._device.actual_angle.animation
        if angle_animation is not None and len(angle_animation.keyframes) > 0:
            _LOGGER.debug(
                "received angle_animation for shutter %s: %s",
                self._uuid,
                angle_animation,
            )
            self._start_moving_device(angle_animation)

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
    def device_class(self) -> Optional[str]:
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

        if (
            self._type
            in (DeviceType.RAFFSTORE_90, DeviceType.RAFFSTORE_180)
            is not None
        ):
            supported_features |= CoverEntityFeature.SET_TILT_POSITION

        return supported_features

    @property
    def current_cover_position(self) -> int:
        """Return current position of cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._device.actual_position
        _LOGGER.debug(
            "received position for device %s: %s",
            self._uuid,
            position,
        )
        return 100 - int(position.value / position.maximum * 100)

    @property
    def current_cover_tilt_position(self) -> int:
        """Return current position of cover tilt.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._device.actual_angle
        _LOGGER.debug(
            "received tilt position for device %s: %s",
            self._uuid,
            position,
        )
        return int(position.value / self._max_angle * 100)

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
        self._set_state(MovingState.OPENING)
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.OPEN), self.hass.loop
        )

    def close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        self._set_state(MovingState.CLOSING)
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.CLOSE),
            self.hass.loop,
        )

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = 100 - int(kwargs.get(ATTR_POSITION))
            hella_position = ceil(
                position * (self._device.target_position.maximum / 100)
            )
            self._calculate_and_set_state(self._device.actual_position.value, position)
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid,
                    {
                        "target_position": hella_position,
                        "target_angle": self._device.target_angle.value,
                    },
                ),
                self.hass.loop,
            )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._set_state(MovingState.STILL)
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.STOP), self.hass.loop
        )

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
            hella_angle = ceil(angle * (self._max_angle / 100))
            self._calculate_and_set_state(
                self._device.actual_angle.value,
                hella_angle,
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid, {"target_angle": hella_angle}
                ),
                self.hass.loop,
            )

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        self._set_state(MovingState.STILL)
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.STOP), self.hass.loop
        )

    def _set_state(self, state: MovingState):
        """Set the new moving state."""
        self._moving_state = state

    def _start_moving_device(self, animation: AnimationValue):
        """Start the update loop."""
        if self._moving_state == MovingState.STILL:
            _LOGGER.debug("not moving still device %s", self._uuid)
            return

        keyframe = animation.keyframes[len(animation.keyframes) - 1]

        current_time = time.time()
        end_time = (
            animation.start
            + keyframe.duration
            + keyframe.delay
            + INCREASED_INTERVAL_DELTA
        )
        is_moving = current_time < end_time

        _LOGGER.debug(
            "moving device %s with current_time %s < end_time %s: %s",
            self._uuid,
            current_time,
            end_time,
            is_moving,
        )

        if is_moving:
            async_track_point_in_utc_time(
                self.hass,
                self._end_moving_device,
                utcnow() + timedelta(seconds=end_time - current_time),
            )
        else:
            self._end_moving_device()

    def _end_moving_device(self, *args: Any):
        """Call STOP to update the device values on ONYX."""
        _LOGGER.debug("ending moving device %s", self._uuid)

        position_animation = self._device.actual_position.animation
        position_keyframe = (
            position_animation.keyframes[len(position_animation.keyframes) - 1]
            if position_animation is not None and len(position_animation.keyframes) > 0
            else None
        )
        position_start_time = (
            (position_animation.start + position_keyframe.delay)
            if position_keyframe is not None and position_animation is not None
            else None
        )
        position_end_time = (
            (position_start_time + position_keyframe.duration)
            if position_keyframe is not None and position_start_time is not None
            else None
        )

        angle_animation = self._device.actual_angle.animation
        angle_keyframe = (
            angle_animation.keyframes[len(angle_animation.keyframes) - 1]
            if angle_animation is not None and len(angle_animation.keyframes) > 0
            else None
        )
        angle_start_time = (
            (angle_animation.start + angle_keyframe.delay)
            if angle_keyframe is not None and angle_animation is not None
            else None
        )
        angle_end_time = (
            (angle_start_time + angle_keyframe.duration)
            if angle_keyframe is not None and angle_start_time is not None
            else None
        )

        current_time = time.time()

        if self._moving_state != MovingState.STILL:
            if (
                (
                    angle_end_time is None
                    and position_end_time is not None
                    and current_time > position_end_time
                )
                or (
                    position_end_time is None
                    and angle_end_time is not None
                    and current_time > angle_end_time
                )
                or (
                    position_end_time is not None
                    and angle_end_time is not None
                    and current_time > position_end_time
                    and current_time > angle_end_time
                )
            ):
                self.stop_cover()
            elif (
                position_start_time is not None and current_time > position_start_time
            ) or (angle_start_time is not None and current_time > angle_start_time):
                if position_animation is not None and position_keyframe.duration > 0:
                    update = interpolate(
                        position_animation.current_value,
                        self._device.target_position.value,
                        position_keyframe.duration,
                        current_time,
                        position_start_time,
                    )
                    _LOGGER.debug(
                        "interpolating actual_position update for device %s: %d",
                        self._uuid,
                        update,
                    )
                    self._device.actual_position.value = update
                if angle_animation is not None and angle_keyframe.duration > 0:
                    update = interpolate(
                        angle_animation.current_value,
                        self._device.target_angle.value,
                        angle_keyframe.duration,
                        current_time,
                        angle_start_time,
                    )
                    _LOGGER.debug(
                        "interpolating actual_angle update for device %s: %d",
                        self._uuid,
                        update,
                    )
                    self._device.actual_angle.value = update

            self.schedule_update_ha_state()

    def _calculate_and_set_state(self, actual: int, new_value: int):
        """Calculate and set the new moving state."""
        new_state = self._calculate_state(actual, new_value)
        self._set_state(new_state)

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
    def _calculate_state(actual: int, new_value: int) -> MovingState:
        """Calculate the new moving state."""
        if new_value < actual:
            return MovingState.OPENING
        elif new_value > actual:
            return MovingState.CLOSING
        else:
            return MovingState.STILL
