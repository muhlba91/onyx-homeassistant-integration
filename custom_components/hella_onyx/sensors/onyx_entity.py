"""The ONYX entity."""

import logging
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from onyx_client.data.numeric_value import NumericValue
from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# fire the end timer after the animation ended, also with clock jitter
END_MARGIN = 0.1


class OnyxEntity(CoordinatorEntity):
    """An ONYX entity.

    Only updates of its own device trigger a state write. Animated values are
    computed at read time; while an animation runs, timers write the state.
    """

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a ONYX entity."""
        super().__init__(api, context=uuid)
        self.api = api
        self.timezone = timezone
        self._name = name
        self._type = device_type
        self._uuid = uuid
        self._animation_unsubs: list[Callable[[], None]] = []

    async def async_added_to_hass(self) -> None:
        """Animate a device which is already moving."""
        await super().async_added_to_hass()
        self._schedule_animation_updates(self._animated_values)

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the pending animation timers."""
        self._cancel_animation_updates()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._schedule_animation_updates(self._animated_values)
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return if the device is known to the ONYX.CENTER."""
        return super().available and self._device is not None

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:help"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._uuid)},
            name=self._name,
            manufacturer="Hella",
            model=self._type.string(),
        )

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Device"

    @property
    def _animated_values(self) -> list[NumericValue | None]:
        """The values whose animations are shown."""
        return []

    @property
    def _device(self):
        """Get the underlying device, or None if it is no longer known."""
        return self.api.device(self._uuid)

    def _numeric_value(self, key: str, divisor: int = 1) -> float | None:
        """The value of a numeric property, divided by the divisor, if known."""
        value = getattr(self._device, key, None)
        if value is None or value.value is None:
            return None
        return value.value / divisor

    def _end_time(self, values: list[NumericValue | None]) -> float | None:
        """End of the latest running animation, including the additional delay."""
        now = self.api.now() - self.api.config.additional_delay / 1000
        end_times = [
            value.animation.end_time()
            for value in values
            if value is not None and value.is_animating(now)
        ]
        if not end_times:
            return None
        return max(end_times) + self.api.config.additional_delay / 1000

    def _schedule_animation_updates(self, values: list[NumericValue | None]):
        """Write the state while any of the values is animated, and at its end."""
        self._cancel_animation_updates()
        end_time = self._end_time(values)
        if end_time is None:
            return

        frequency = self.api.config.interpolation_frequency
        if frequency > 0:
            self._animation_unsubs.append(
                async_track_time_interval(
                    self.hass,
                    self._handle_animation_update,
                    timedelta(seconds=frequency),
                )
            )
        self._animation_unsubs.append(
            async_call_later(
                self.hass,
                end_time - self.api.now() + END_MARGIN,
                self._handle_animation_end,
            )
        )
        _LOGGER.debug("animating device %s until %s", self._uuid, end_time)

    def _cancel_animation_updates(self):
        """Cancel the pending animation timers."""
        for unsub in self._animation_unsubs:
            unsub()
        self._animation_unsubs = []

    @callback
    def _handle_animation_update(self, *args: Any):
        """Write the interpolated state."""
        self.async_write_ha_state()

    @callback
    def _handle_animation_end(self, *args: Any):
        """Write the end state."""
        self._cancel_animation_updates()
        self.async_write_ha_state()
