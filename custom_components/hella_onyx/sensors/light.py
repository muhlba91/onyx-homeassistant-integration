"""The ONYX light entity."""
import asyncio
import logging
import time
from datetime import timedelta
from math import ceil
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    LightEntityFeature,
    ATTR_BRIGHTNESS,
)
from homeassistant.helpers.event import (
    track_point_in_utc_time,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import utcnow
from onyx_client.data.animation_value import AnimationValue
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType
from onyx_client.data.numeric_value import NumericValue

from custom_components.hella_onyx.api_connector import APIConnector
from custom_components.hella_onyx.const import INCREASED_INTERVAL_DELTA
from custom_components.hella_onyx.sensors.onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)

MIN_USED_DIM_DURATION = 500
MAX_USED_DIM_DURATION = 6000


class OnyxLight(OnyxEntity, LightEntity):
    """A light entity."""

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        coordinator: DataUpdateCoordinator,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a light entity."""
        super().__init__(api, timezone, coordinator, name, device_type, uuid)

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:lightbulb-on-outline"

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Light"

    @property
    def supported_features(self):
        """Flag supported features."""
        return LightEntityFeature(0)

    @property
    def color_mode(self) -> ColorMode | str | None:
        """Return the color mode of the light."""
        return (
            ColorMode.ONOFF
            if self._device.device_type == DeviceType.BASIC_LIGHT
            else ColorMode.BRIGHTNESS
        )

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        return [self.color_mode]

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        brightness = self._actual_brightness
        _LOGGER.debug(
            "received brightness for light %s: %s",
            self._uuid,
            brightness,
        )
        if (
            brightness.animation is not None
            and len(brightness.animation.keyframes) > 0
            and brightness.animation.keyframes[
                len(brightness.animation.keyframes) - 1
            ].value
            != brightness.value
        ):
            self._start_update_device(brightness.animation)
        return brightness.value / brightness.maximum * 255

    @property
    def is_on(self) -> bool | None:
        """Return whether the light is turned on."""
        return self._actual_brightness.value > 0

    def turn_on(self, **kwargs: Any) -> None:
        """Turns the light on."""
        brightness_attribute = kwargs.pop(ATTR_BRIGHTNESS, None)
        if brightness_attribute is None:
            _LOGGER.debug(
                "turning light %s on",
                self._uuid,
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_action(
                    self._uuid,
                    Action.LIGHT_ON,
                ),
                self.hass.loop,
            )
        else:
            hella_brightness = ceil(
                brightness_attribute / 255 * self._device.actual_brightness.maximum
            )
            dim_duration = self._get_dim_duration(hella_brightness)
            _LOGGER.debug(
                "setting brightness for light %s: %s (%s ms)",
                self._uuid,
                hella_brightness,
                dim_duration,
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid,
                    {
                        "target_brightness": hella_brightness,
                        "dim_duration": dim_duration,
                    },
                ),
                self.hass.loop,
            )

    def turn_off(self, **kwargs: Any) -> None:
        """Turns the light off."""
        _LOGGER.debug(
            "turning light %s off",
            self._uuid,
        )
        asyncio.run_coroutine_threadsafe(
            self.api.send_device_command_action(self._uuid, Action.LIGHT_OFF),
            self.hass.loop,
        )

    def _start_update_device(self, animation: AnimationValue):
        """Start the update loop."""
        keyframes = len(animation.keyframes)
        keyframe = animation.keyframes[keyframes - 1]

        current_time = time.time()
        end_time = animation.start + keyframe.duration + keyframe.delay
        delta = end_time - current_time
        updating = current_time < end_time

        _LOGGER.debug(
            "updating device %s with current_time %s and end_time %s: %s",
            self._uuid,
            current_time,
            end_time,
            updating,
        )

        if updating:
            track_point_in_utc_time(
                self.hass,
                self._end_update_device,
                utcnow() + timedelta(seconds=delta + INCREASED_INTERVAL_DELTA),
            )

    def _end_update_device(self, *args: Any):
        """Call STOP to update the device values on ONYX."""
        animation = self._actual_brightness.animation
        keyframe = (
            animation.keyframes[len(animation.keyframes) - 1]
            if animation is not None and len(animation.keyframes) > 0
            else None
        )
        start_time = (
            (animation.start + keyframe.delay) if keyframe is not None else None
        )
        end_time = (start_time + keyframe.duration) if keyframe is not None else None

        current_time = time.time()

        if current_time > end_time:
            _LOGGER.debug(
                "calling stop to force update device %s",
                self._uuid,
            )
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_action(
                    self._uuid,
                    Action.STOP,
                ),
                self.hass.loop,
            )
        elif current_time > start_time:
            delta = current_time - start_time
            delta_per_unit = (
                self._device.target_brightness.value - animation.current_value
            ) / keyframe.duration
            update = ceil(animation.current_value + delta_per_unit * delta)
            _LOGGER.debug(
                "interpolating brightness update for device %s: %d",
                self._uuid,
                update,
            )
            self._device.actual_brightness.value = update
            self.async_write_ha_state()

    @property
    def _actual_brightness(self) -> NumericValue:
        """Get the actual brightness."""
        brightness = self._device.actual_brightness
        return NumericValue(
            0 if brightness.value is None else brightness.value,
            brightness.minimum,
            brightness.maximum,
            brightness.read_only,
            brightness.animation,
        )

    def _get_dim_duration(self, target) -> int:
        """Get the dim duration."""
        brightness = self._actual_brightness
        return abs(
            int(
                (target - brightness.value)
                / brightness.maximum
                * (MAX_USED_DIM_DURATION - MIN_USED_DIM_DURATION)
                + MIN_USED_DIM_DURATION
            )
        )
