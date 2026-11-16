"""The ONYX light entity."""

import logging
from math import ceil
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from onyx_client.data.numeric_value import NumericValue
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector
from ..sensors.onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)


class OnyxLight(OnyxEntity, LightEntity):
    """A light entity."""

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
        return (
            ColorMode.ONOFF
            if self._type == DeviceType.BASIC_LIGHT
            else ColorMode.BRIGHTNESS
        )

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        mode = self.color_mode
        return {mode} if mode else None

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
        if brightness_attribute is None:
            _LOGGER.debug(
                "turning light %s on",
                self._uuid,
            )
            await self.api.send_device_command_action(
                self._uuid,
                Action.LIGHT_ON,
            )
        else:
            brightness = self._actual_brightness
            target_max = (
                brightness.maximum if brightness and brightness.maximum else 255
            )
            hella_brightness = ceil(brightness_attribute / 255 * target_max)
            dim_duration = self._get_dim_duration(hella_brightness, target_max)
            _LOGGER.debug(
                "setting brightness for light %s: %s (%s ms)",
                self._uuid,
                hella_brightness,
                dim_duration,
            )
            await self.api.send_device_command_properties(
                self._uuid,
                {
                    "target_brightness": hella_brightness,
                    "dim_duration": dim_duration,
                },
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
        return [self._actual_brightness]

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
