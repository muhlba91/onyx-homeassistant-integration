"""The ONYX shutter entity."""
import asyncio
import logging
from typing import Any, Callable, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device import shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from . import APIConnector, DOMAIN
from .const import ONYX_API, ONYX_COORDINATOR
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
        Shutter(api, coordinator, device.name, device.device_type, device_id)
        for device_id, device in api.devices.items()
    ]
    _LOGGER.debug("adding %s hella_onyx entities", len(shutters))
    async_add_entities(shutters, True)


class Shutter(OnyxEntity, CoverEntity):
    """A shutter entity."""

    def __init__(
        self,
        api: APIConnector,
        coordinator: DataUpdateCoordinator,
        name: str,
        type: DeviceType,
        uuid: str,
    ):
        """Initialize a shutter entity."""
        super().__init__(api, coordinator, name, type, uuid)
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
    def supported_features(self):
        """Flag supported features."""
        supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

        if self.current_cover_position is not None:
            supported_features |= SUPPORT_SET_POSITION

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
        return (position.maximum - position.value) / position.maximum * 100

    @property
    def current_cover_tilt_position(self) -> int:
        """Return current position of cover tilt.

        None is unknown, 0 is closed, 100 is fully open.
        """
        position = self._device.actual_angle
        return (position.maximum - position.value) / position.maximum * 100

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
            position = int(kwargs.get(ATTR_POSITION))
            self._calculate_and_set_state(self._device.actual_position, position)
            asyncio.run_coroutine_threadsafe(
                self.api.send_device_command_properties(
                    self._uuid, {"target_position": position}
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
            hella_angle = int(angle * (self._max_angle / 100))
            self._calculate_and_set_state(self._device.actual_angle, hella_angle)
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

    def _calculate_state(self, actual: NumericValue, new_value: int) -> MovingState:
        """Calculate the new moving state."""
        if new_value < actual.value:
            return MovingState.CLOSING
        elif new_value > actual.value:
            return MovingState.OPENING
        else:
            return MovingState.STILL

    def _calculate_and_set_state(self, actual: NumericValue, new_value: int):
        """Calculate and set the new moving state."""
        self._set_state(self._calculate_state(actual, new_value))

    @property
    def _device(self) -> shutter.Shutter:
        """Get the underlying device."""
        return self.api.device(self._uuid)

    @property
    def _max_angle(self) -> int:
        """Maximum angle depending on raffstore type."""
        if self._type == DeviceType.RAFFSTORE_90:
            return 90
        elif self._type == DeviceType.RAFFSTORE_180:
            return 180
        else:
            return 100
