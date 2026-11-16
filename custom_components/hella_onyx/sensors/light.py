"""The ONYX light entity."""

import logging
from math import ceil
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.numeric_value import NumericValue
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector
from ..const import (
    COLOR_MODE_TEMPERATURE,
    DEFAULT_MAX_COLOR_TEMPERATURE,
    DEFAULT_MIN_COLOR_TEMPERATURE,
)
from ..sensors.onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)


class OnyxLight(OnyxEntity, LightEntity):
    """A light entity.

    RGBW lights (experimental) show either a color (hue and saturation) or a
    white tone (color temperature), as reported by the ONYX.CENTER.
    """

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a light entity."""
        super().__init__(api, timezone, name, device_type, uuid)

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
        if self._type == DeviceType.BASIC_LIGHT:
            return ColorMode.ONOFF
        if self._type != DeviceType.RGBW_LIGHT:
            return ColorMode.BRIGHTNESS
        device = self._device
        mode = device.color_mode if device else None
        if mode is not None and mode.value == COLOR_MODE_TEMPERATURE:
            return ColorMode.COLOR_TEMP
        return ColorMode.HS

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        if self._type == DeviceType.RGBW_LIGHT:
            return {ColorMode.HS, ColorMode.COLOR_TEMP}
        return {self.color_mode}

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue (0..360) and saturation (0..100) of an RGBW light."""
        hue = self._effective_hue()
        saturation = self._effective(self._value("actual_saturation"))
        if hue is None or saturation is None:
            return None
        return hue, saturation

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature of an RGBW light in Kelvin."""
        kelvin = self._effective(self._value("actual_color_temperature"))
        return None if kelvin is None else round(kelvin)

    @property
    def min_color_temp_kelvin(self) -> int:
        """Return the warmest supported color temperature in Kelvin."""
        return self._color_temperature_range()[0]

    @property
    def max_color_temp_kelvin(self) -> int:
        """Return the coldest supported color temperature in Kelvin."""
        return self._color_temperature_range()[1]

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        brightness = self._actual_brightness
        if not brightness or not brightness.maximum:
            return 0
        return round(self._effective_brightness() / brightness.maximum * 255)

    @property
    def is_on(self) -> bool | None:
        """Return whether the light is turned on."""
        if not self._actual_brightness:
            return None
        return self._effective_brightness() > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turns the light on."""
        brightness_attribute = kwargs.pop(ATTR_BRIGHTNESS, None)
        properties = self._color_properties(
            kwargs.pop(ATTR_HS_COLOR, None), kwargs.pop(ATTR_COLOR_TEMP_KELVIN, None)
        )
        brightness = self._actual_brightness
        target_max = brightness.maximum if brightness and brightness.maximum else 255
        hella_brightness = None
        if brightness_attribute is not None:
            hella_brightness = ceil(brightness_attribute / 255 * target_max)
        elif properties and not self.is_on:
            # a new command cancels the previous one, so a color of a light
            # which is off is sent together with a brightness instead of LIGHT_ON
            hella_brightness = self._target_brightness(target_max)
        if hella_brightness is not None:
            properties["target_brightness"] = hella_brightness
            properties["dim_duration"] = self._get_dim_duration(
                hella_brightness, target_max
            )
        if properties:
            _LOGGER.debug("setting light %s: %s", self._uuid, properties)
            await self.api.send_device_command_properties(self._uuid, properties)
        else:
            _LOGGER.debug(
                "turning light %s on",
                self._uuid,
            )
            await self.api.send_device_command_action(
                self._uuid,
                Action.LIGHT_ON,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turns the light off."""
        _LOGGER.debug(
            "turning light %s off",
            self._uuid,
        )
        await self.api.send_device_command_action(self._uuid, Action.LIGHT_OFF)

    @property
    def _animated_values(self) -> list[NumericValue | None]:
        return [
            self._actual_brightness,
            self._value("actual_hue"),
            self._value("actual_saturation"),
            self._value("actual_color_temperature"),
        ]

    def _value(self, key: str) -> NumericValue | None:
        """A numeric property of the device, if known."""
        return getattr(self._device, key, None)

    def _effective(self, value: NumericValue | None) -> float | None:
        """The value at the current ONYX.CENTER time, if known."""
        return value.effective_value(self.api.now()) if value else None

    def _effective_hue(self) -> float | None:
        """The hue at the current ONYX.CENTER time, if known.

        Hue animations take the shortest way around the color wheel, e.g.
        from 350 over 0 to 10 degrees.
        """
        hue = self._value("actual_hue")
        if hue is None:
            return None
        animation = hue.animation
        if animation is None or not animation.keyframes:
            value = hue.value
        else:
            value = _shortest_hue_path(animation).value_at(self.api.now())
        return None if value is None else value % 360

    def _target_brightness(self, maximum: int) -> int:
        """The reported target brightness if it is on, else the maximum."""
        target = self._value("target_brightness")
        if target is None or not target.value or target.value > maximum:
            return maximum
        return target.value

    def _color_temperature_range(self) -> tuple[int, int]:
        """The supported color temperature range in Kelvin."""
        kelvin = self._value("target_color_temperature") or self._value(
            "actual_color_temperature"
        )
        minimum = kelvin.minimum if kelvin else None
        maximum = kelvin.maximum if kelvin else None
        if minimum is None or maximum is None or minimum >= maximum:
            return DEFAULT_MIN_COLOR_TEMPERATURE, DEFAULT_MAX_COLOR_TEMPERATURE
        return minimum, maximum

    def _color_properties(
        self, hs_color: tuple[float, float] | None, kelvin: int | None
    ) -> dict:
        """The properties to set the color or white tone of an RGBW light.

        Home Assistant passes one of both; a color wins over a white tone.
        """
        if self._type != DeviceType.RGBW_LIGHT:
            return {}
        if hs_color is not None:
            hue, saturation = hs_color
            return {
                "target_hue": round(hue) % 360,
                "target_saturation": min(max(round(saturation), 0), 100),
            }
        if kelvin is not None:
            minimum, maximum = self._color_temperature_range()
            return {
                "target_color_temperature": min(max(round(kelvin), minimum), maximum)
            }
        return {}

    @property
    def _actual_brightness(self) -> NumericValue | None:
        device = self._device
        return device.actual_brightness if device else None

    def _effective_brightness(self) -> float:
        """The brightness at the current ONYX.CENTER time; unknown is 0."""
        brightness = self._actual_brightness
        value = brightness.effective_value(self.api.now()) if brightness else None
        return 0 if value is None else value

    def _get_dim_duration(self, target: int, maximum: int) -> int:
        """Get the dim duration within the configured and the device's range."""
        duration = abs(
            int(
                abs(target - self._effective_brightness())
                / maximum
                * (self.api.config.max_dim_duration - self.api.config.min_dim_duration)
                + self.api.config.min_dim_duration
            )
        )
        duration = min(duration, self.api.config.max_dim_duration)
        device = self._device
        device_range = device.dim_duration if device else None
        if device_range is not None:
            # the device minimum wins over an inconsistent maximum
            if device_range.maximum is not None:
                duration = min(duration, device_range.maximum)
            if device_range.minimum is not None:
                duration = max(duration, device_range.minimum)
        return duration


def _shortest_hue_path(animation: AnimationValue) -> AnimationValue:
    """The animation with each hue keyframe moved to the nearest equivalent angle."""
    previous = animation.current_value
    keyframes = []
    for keyframe in animation.keyframes:
        value = keyframe.value
        if value is not None:
            value = previous + (value - previous + 180) % 360 - 180
            previous = value
        keyframes.append(
            AnimationKeyframe(
                value, keyframe.duration, keyframe.delay, keyframe.interpolation
            )
        )
    return AnimationValue(animation.start, animation.current_value, keyframes)
