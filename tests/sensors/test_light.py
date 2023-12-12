"""Test for the ONYX Light Entity."""
from unittest.mock import MagicMock, patch

import pytest
import time
import pytz
from datetime import datetime
from homeassistant.components.light import (
    ColorMode,
    brightness_supported,
)
from homeassistant.core import HomeAssistant
from onyx_client.data.numeric_value import NumericValue
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.device.light import Light
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.light import OnyxLight


class TestOnyxLight:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def coordinator(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        hass = MagicMock(spec=HomeAssistant)
        hass.loop = MagicMock()
        yield hass

    @pytest.fixture
    def entity(self, api, coordinator, hass):
        shutter = OnyxLight(
            api, "UTC", coordinator, "name", DeviceType.BASIC_LIGHT, "uuid"
        )
        shutter.hass = hass
        yield shutter

    @pytest.fixture
    def dimmable_entity(self, api, coordinator):
        yield OnyxLight(
            api, "UTC", coordinator, "name", DeviceType.DIMMABLE_LIGHT, "uuid"
        )

    @pytest.fixture
    def device(self):
        yield Light(
            "id",
            "name",
            DeviceType.BASIC_LIGHT,
            None,
            list(Action),
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:lightbulb-on-outline"

    def test_name(self, entity):
        assert entity.name == "name"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Light"

    def test_supported_features(self, entity):
        assert entity.supported_features == 0

    def test_color_mode_basic_light(self, api, entity, device):
        device.device_type = DeviceType.BASIC_LIGHT
        api.device.return_value = device
        assert entity.color_mode == ColorMode.ONOFF
        assert len(entity.supported_color_modes) == 1
        assert entity.supported_color_modes[0] == ColorMode.ONOFF
        assert api.device.called
        assert brightness_supported(entity.supported_color_modes) is False

    def test_color_mode_dimmable_light(self, api, dimmable_entity, device):
        device.device_type = DeviceType.DIMMABLE_LIGHT
        api.device.return_value = device
        assert dimmable_entity.color_mode == ColorMode.BRIGHTNESS
        assert len(dimmable_entity.supported_color_modes) == 1
        assert dimmable_entity.supported_color_modes[0] == ColorMode.BRIGHTNESS
        assert api.device.called
        assert brightness_supported(dimmable_entity.supported_color_modes) is True

    def test_brightness(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.brightness == 25.5
        assert api.device.called

    def test_brightness_with_animation(self, api, entity, device):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=20
                )
            ],
        )
        device.actual_brightness = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        api.device.return_value = device
        with patch.object(entity, "_start_update_device") as mock_start_update_device:
            assert entity.brightness == 25.5
            mock_start_update_device.assert_called_with(animation)
            assert api.device.called

    def test_brightness_with_old_animation(self, api, entity, device):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=10
                )
            ],
        )
        device.actual_brightness = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        api.device.return_value = device
        with patch.object(entity, "_start_update_device") as mock_start_update_device:
            assert entity.brightness == 25.5
            mock_start_update_device.assert_not_called
            assert api.device.called

    def test_is_on(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.is_on
        assert api.device.called

    def test_is_on_off(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert not entity.is_on
        assert api.device.called

    def test_is_on_none(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=None, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert not entity.is_on
        assert api.device.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_turn_off(self, mock_run_coroutine_threadsafe, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        entity.turn_off()
        api.send_device_command_action.assert_called_with("uuid", Action.LIGHT_OFF)
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_turn_on(self, mock_run_coroutine_threadsafe, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        entity.turn_on(brightness=10)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_brightness": 4,
                "dim_duration": 4780,
            },
        )
        assert mock_run_coroutine_threadsafe.called
        assert api.device.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_turn_on_no_brightness(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        entity.turn_on()
        api.send_device_command_action.assert_called_with(
            "uuid",
            Action.LIGHT_ON,
        )
        assert mock_run_coroutine_threadsafe.called
        assert not api.device.called

    def test__get_dim_duration(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=14645, maximum=65535, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(31) == 726
        assert api.device.called

    def test__actual_brightness_no_value(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=None, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._actual_brightness == NumericValue(0, 0, 100, False)
        assert api.device.called

    def test__actual_brightness(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=1, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._actual_brightness == NumericValue(1, 0, 100, False)
        assert api.device.called

    def test__get_dim_duration_same(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(100) == 500
        assert api.device.called

    def test__get_dim_duration_invalid_value(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=None, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(90) == 5450
        assert api.device.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_start_update_device_end(self, api, entity, device):
        current_time = time.mktime(datetime.now(pytz.timezone("UTC")).timetuple())
        animation = AnimationValue(
            start=current_time - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=10,
                    delay=0,
                )
            ],
        )
        with patch.object(entity, "_end_update_device") as mock_end_update_device:
            entity._start_update_device(animation)
            mock_end_update_device.assert_not_called()

    @patch("asyncio.run_coroutine_threadsafe")
    def test__end_update_device(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
        device.actual_brightness = NumericValue(
            value=None,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time() - 1000, 10, [AnimationKeyframe("linear", 0, 100, 90)]
            ),
        )
        api.device.return_value = device
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            entity._end_update_device()
            assert api.device.called
            assert not mock_async_write_ha_state.called
            assert mock_run_coroutine_threadsafe.called
            api.send_device_command_action.assert_called_with("uuid", Action.STOP)

    @patch("asyncio.run_coroutine_threadsafe")
    def test__end_update_device_within_time(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
        device.actual_brightness = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time(), 0, [AnimationKeyframe("linear", 0, 20000, 50)]
            ),
        )
        device.target_brightness = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            entity._end_update_device()
            assert api.device.called
            assert mock_async_write_ha_state.called
            assert not mock_run_coroutine_threadsafe.called
            assert entity._device.actual_brightness.value == 1

    @patch("asyncio.run_coroutine_threadsafe")
    def test__end_update_device_within_time_using_delay(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
        device.actual_brightness = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time() - 100, 0, [AnimationKeyframe("linear", 100000, 10, 50)]
            ),
        )
        device.target_brightness = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            entity._end_update_device()
            assert api.device.called
            assert not mock_async_write_ha_state.called
            assert not mock_run_coroutine_threadsafe.called
