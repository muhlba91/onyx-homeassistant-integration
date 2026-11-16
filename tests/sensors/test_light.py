"""Test for the ONYX Light Entity."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.light import ColorMode, LightEntityFeature
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.light import Light
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.const import (
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
)
from custom_components.hella_onyx.light import OnyxLight

from .helpers import NOW, animated, make_api, value


class TestOnyxLight:
    @pytest.fixture
    def api(self):
        yield make_api()

    @pytest.fixture
    def device(self, api):
        device = Light(
            "uuid",
            "name",
            DeviceType.DIMMABLE_LIGHT,
            DeviceMode(DeviceType.DIMMABLE_LIGHT),
            list(Action),
            target_brightness=value(100),
            actual_brightness=value(100),
        )
        api.device.return_value = device
        yield device

    def create(self, api, device_type=DeviceType.DIMMABLE_LIGHT):
        entity = OnyxLight(api, "UTC", "name", device_type, "uuid")
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        return entity

    @pytest.fixture
    def entity(self, api):
        yield self.create(api)

    def test_properties(self, entity):
        assert entity.icon == "mdi:lightbulb-on-outline"
        assert entity.name == "name"
        assert entity.unique_id == "uuid/Light"
        assert entity.supported_features == LightEntityFeature(0)

    def test_color_mode(self, api, entity):
        assert entity.color_mode == ColorMode.BRIGHTNESS
        assert entity.supported_color_modes == {ColorMode.BRIGHTNESS}
        basic = self.create(api, DeviceType.BASIC_LIGHT)
        assert basic.color_mode == ColorMode.ONOFF
        assert basic.supported_color_modes == {ColorMode.ONOFF}
        assert (
            self.create(api, DeviceType.RGBW_LIGHT).color_mode == ColorMode.BRIGHTNESS
        )

    def test_brightness(self, entity, device):
        device.actual_brightness = value(50)
        assert entity.brightness == 128
        assert entity.is_on
        device.actual_brightness = value(0)
        assert entity.brightness == 0
        assert not entity.is_on

    def test_brightness_unknown(self, api, entity, device):
        device.actual_brightness = value(None)
        assert entity.brightness == 0
        assert not entity.is_on
        device.actual_brightness = value(10, 0)
        assert entity.brightness == 0
        api.device.return_value = None
        assert entity.brightness == 0
        assert entity.is_on is None

    def test_brightness_during_animation(self, entity, device):
        device.actual_brightness = animated(0, 100, NOW - 1, 2)
        assert entity.brightness == 128
        assert entity.is_on

    def test_brightness_after_natural_end(self, entity, device):
        # the device keeps reporting the start value after the animation ended
        device.actual_brightness = animated(100, 0, NOW - 100, 2)
        assert entity.brightness == 0
        assert not entity.is_on

    def test_animated_values(self, entity, device):
        assert entity._animated_values == [device.actual_brightness]

    async def test_turn_on(self, api, entity, device):
        await entity.async_turn_on()
        api.send_device_command_action.assert_called_once_with("uuid", Action.LIGHT_ON)

    async def test_turn_on_brightness(self, api, entity, device):
        await entity.async_turn_on(brightness=10)
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_brightness": 4, "dim_duration": 1928}
        )

    async def test_turn_on_brightness_scaled(self, api, entity, device):
        device.actual_brightness = value(65535, 65535)
        await entity.async_turn_on(brightness=255)
        api.send_device_command_properties.assert_called_once_with(
            "uuid",
            {"target_brightness": 65535, "dim_duration": DEFAULT_MIN_DIM_DURATION},
        )

    async def test_turn_on_brightness_unknown_maximum(self, api, entity):
        api.device.return_value = None
        await entity.async_turn_on(brightness=255)
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_brightness": 255, "dim_duration": DEFAULT_MAX_DIM_DURATION}
        )

    async def test_turn_off(self, api, entity):
        await entity.async_turn_off()
        api.send_device_command_action.assert_called_once_with("uuid", Action.LIGHT_OFF)

    def test_get_dim_duration(self, api, entity, device):
        device.actual_brightness = value(14645, 65535)
        assert entity._get_dim_duration(31, 65535) == 601
        api.config.max_dim_duration = 1000
        assert entity._get_dim_duration(31, 65535) == 378
        api.config.min_dim_duration = 2000
        assert entity._get_dim_duration(31, 65535) == 1000

    def test_get_dim_duration_bounds(self, entity, device):
        assert entity._get_dim_duration(100, 100) == DEFAULT_MIN_DIM_DURATION
        device.actual_brightness = value(0, 65535)
        assert entity._get_dim_duration(65535, 65535) == DEFAULT_MAX_DIM_DURATION
        device.actual_brightness = value(65535, 100)
        assert entity._get_dim_duration(0, 100) == DEFAULT_MAX_DIM_DURATION
        device.actual_brightness = value(None)
        assert entity._get_dim_duration(90, 100) == 1820

    def test_get_dim_duration_during_animation(self, entity, device):
        device.actual_brightness = animated(0, 100, NOW - 1, 2)
        assert entity._get_dim_duration(50, 100) == DEFAULT_MIN_DIM_DURATION
