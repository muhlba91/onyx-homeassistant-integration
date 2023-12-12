"""The ONYX light entity."""
import asyncio
import logging
from math import ceil
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.api_connector import APIConnector
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
        return []

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
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        brightness = self._device.actual_brightness
        _LOGGER.debug(
            "received brightness for light %s: %s",
            self._uuid,
            brightness,
        )
        return brightness.value / brightness.maximum * 255

    def turn_on(self, **kwargs: Any) -> None:
        """Turns the light on."""
        hella_brightness = ceil(
            kwargs[ATTR_BRIGHTNESS] / 255 * self._device.actual_brightness.maximum
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

    def _get_dim_duration(self, target) -> int:
        """Get the dim duration."""
        brightness = self._device.actual_brightness
        return abs(
            int(
                (target - brightness.value)
                / brightness.maximum
                * (MAX_USED_DIM_DURATION - MIN_USED_DIM_DURATION)
                + MIN_USED_DIM_DURATION
            )
        )
