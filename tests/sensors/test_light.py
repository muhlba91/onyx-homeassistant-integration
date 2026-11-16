"""Test for the ONYX Light Entity."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.light import ColorMode, LightEntityFeature
from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.enum_value import EnumValue
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.light import Light
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.const import (
    DEFAULT_MAX_COLOR_TEMPERATURE,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_COLOR_TEMPERATURE,
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

    def test_no_colors(self, entity, device):
        assert entity.hs_color is None
        assert entity.color_temp_kelvin is None

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
        assert entity._animated_values == [device.actual_brightness, None, None, None]

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

    def test_get_dim_duration_device_range(self, entity, device):
        device.actual_brightness = value(0, 65535)
        device.dim_duration = NumericValue(None, 0, 1500, False)
        assert entity._get_dim_duration(65535, 65535) == 1500
        assert entity._get_dim_duration(0, 65535) == DEFAULT_MIN_DIM_DURATION
        device.dim_duration = NumericValue(None, 300, 5000, False)
        assert entity._get_dim_duration(0, 65535) == 300
        assert entity._get_dim_duration(65535, 65535) == DEFAULT_MAX_DIM_DURATION
        device.dim_duration = NumericValue(None, None, None, False)
        assert entity._get_dim_duration(0, 65535) == DEFAULT_MIN_DIM_DURATION
        assert entity._get_dim_duration(65535, 65535) == DEFAULT_MAX_DIM_DURATION

    def test_get_dim_duration_device_range_unknown_device(self, api, entity):
        api.device.return_value = None
        assert entity._get_dim_duration(255, 255) == DEFAULT_MAX_DIM_DURATION

    def test_get_dim_duration_during_animation(self, entity, device):
        device.actual_brightness = animated(0, 100, NOW - 1, 2)
        assert entity._get_dim_duration(50, 100) == DEFAULT_MIN_DIM_DURATION


class TestOnyxRgbwLight:
    @pytest.fixture
    def api(self):
        yield make_api()

    @pytest.fixture
    def device(self, api):
        device = Light(
            "uuid",
            "name",
            DeviceType.RGBW_LIGHT,
            DeviceMode(DeviceType.RGBW_LIGHT),
            list(Action),
            target_brightness=value(65535, 65535),
            actual_brightness=value(65535, 65535),
            target_hue=value(120, 359),
            actual_hue=value(120, 359),
            target_saturation=value(50),
            actual_saturation=value(50),
            target_color_temperature=NumericValue(4000, 3000, 6500, False),
            actual_color_temperature=NumericValue(4000, 3000, 6500, False),
            color_mode=EnumValue("hsv", ["hsv", "temperature"], True),
        )
        api.device.return_value = device
        yield device

    @pytest.fixture
    def entity(self, api, device):
        entity = OnyxLight(api, "UTC", "name", DeviceType.RGBW_LIGHT, "uuid")
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        yield entity

    def test_color_mode(self, entity, device):
        assert entity.supported_color_modes == {ColorMode.HS, ColorMode.COLOR_TEMP}
        assert entity.color_mode == ColorMode.HS
        device.color_mode = EnumValue("temperature", [], True)
        assert entity.color_mode == ColorMode.COLOR_TEMP
        device.color_mode = None
        assert entity.color_mode == ColorMode.HS

    def test_color_mode_unknown_device(self, api, entity):
        api.device.return_value = None
        assert entity.color_mode == ColorMode.HS
        assert entity.hs_color is None
        assert entity.color_temp_kelvin is None

    def test_colors(self, entity):
        assert entity.hs_color == (120, 50)
        assert entity.color_temp_kelvin == 4000
        assert entity.min_color_temp_kelvin == 3000
        assert entity.max_color_temp_kelvin == 6500

    def test_colors_unknown(self, entity, device):
        device.actual_saturation = value(None)
        assert entity.hs_color is None
        device.actual_saturation = value(50)
        device.actual_hue = None
        assert entity.hs_color is None
        device.actual_color_temperature = value(None)
        assert entity.color_temp_kelvin is None

    def test_color_temperature_range_fallback(self, entity, device):
        device.target_color_temperature = None
        device.actual_color_temperature = NumericValue(4000, None, 6500, False)
        assert entity.min_color_temp_kelvin == DEFAULT_MIN_COLOR_TEMPERATURE
        assert entity.max_color_temp_kelvin == DEFAULT_MAX_COLOR_TEMPERATURE
        device.actual_color_temperature = NumericValue(4000, 6500, 6500, False)
        assert entity.min_color_temp_kelvin == DEFAULT_MIN_COLOR_TEMPERATURE
        device.actual_color_temperature = NumericValue(4000, 2000, None, False)
        assert entity.max_color_temp_kelvin == DEFAULT_MAX_COLOR_TEMPERATURE
        device.actual_color_temperature = None
        assert entity.max_color_temp_kelvin == DEFAULT_MAX_COLOR_TEMPERATURE

    def test_color_animations(self, entity, device):
        device.actual_saturation = animated(0, 100, NOW - 1, 2)
        device.actual_color_temperature = animated(3000, 5000, NOW - 1, 2, 6500)
        assert entity.hs_color == (120, 50)
        assert entity.color_temp_kelvin == 4000
        assert entity._animated_values[1:] == [
            device.actual_hue,
            device.actual_saturation,
            device.actual_color_temperature,
        ]

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (350, 10, 0),
            (10, 350, 0),
            # half way round: counter-clockwise
            (0, 180, 270),
            (90, 270, 0),
            (300, 60, 0),
            (350, 370, 0),
        ],
    )
    def test_hue_animation_takes_shortest_path(
        self, entity, device, start, end, expected
    ):
        device.actual_hue = animated(start, end, NOW - 1, 2, 359)
        assert entity.hs_color == (expected, 50)

    def test_hue_animation_keyframes(self, entity, device):
        device.actual_hue = NumericValue(
            350,
            0,
            359,
            False,
            AnimationValue(
                NOW - 3,
                350,
                [
                    AnimationKeyframe(10, 2),
                    AnimationKeyframe(None, 1),
                    AnimationKeyframe(340, 2),
                ],
            ),
        )
        # 10 -> 340 also passes 0: 10, 355 (= -5), at half way
        assert entity.hs_color == (10, 50)
        device.actual_hue.animation.start = NOW - 4
        assert entity.hs_color == (355, 50)
        device.actual_hue.animation.start = NOW - 100
        assert entity.hs_color == (340, 50)

    async def test_turn_on_hs_color(self, api, entity):
        await entity.async_turn_on(hs_color=(359.6, 100.4))
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_hue": 0, "target_saturation": 100}
        )
        assert not api.send_device_command_action.called

    async def test_turn_on_color_temperature(self, api, entity):
        await entity.async_turn_on(color_temp_kelvin=2000)
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_color_temperature": 3000}
        )
        assert not api.send_device_command_action.called

    async def test_turn_on_color_and_brightness(self, api, entity):
        await entity.async_turn_on(brightness=255, color_temp_kelvin=9000)
        api.send_device_command_properties.assert_called_once_with(
            "uuid",
            {
                "target_color_temperature": 6500,
                "target_brightness": 65535,
                "dim_duration": DEFAULT_MIN_DIM_DURATION,
            },
        )
        assert not api.send_device_command_action.called

    async def test_turn_on_color_of_light_off(self, api, entity, device):
        device.actual_brightness = value(0, 65535)
        await entity.async_turn_on(hs_color=(10, 20))
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_hue": 10, "target_saturation": 20}
        )
        api.send_device_command_action.assert_called_once_with("uuid", Action.LIGHT_ON)

    async def test_turn_on_color_of_dimmable_light(self, api):
        entity = OnyxLight(api, "UTC", "name", DeviceType.DIMMABLE_LIGHT, "uuid")
        await entity.async_turn_on(hs_color=(10, 20), color_temp_kelvin=3000)
        assert not api.send_device_command_properties.called
        api.send_device_command_action.assert_called_once_with("uuid", Action.LIGHT_ON)

    async def test_turn_on_without_color(self, api, entity):
        await entity.async_turn_on()
        assert not api.send_device_command_properties.called
        api.send_device_command_action.assert_called_once_with("uuid", Action.LIGHT_ON)
