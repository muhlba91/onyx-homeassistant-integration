"""Test for the ONYX Light Entity."""

import asyncio
import pytest
import time

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

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

from custom_components.hella_onyx.const import (
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ADDITIONAL_DELAY,
)
from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.light import OnyxLight


class TestOnyxLight:
    @pytest.fixture
    def config(self):
        yield Configuration(
            DEFAULT_SCAN_INTERVAL,
            DEFAULT_MIN_DIM_DURATION,
            DEFAULT_MAX_DIM_DURATION,
            DEFAULT_ADDITIONAL_DELAY,
            DEFAULT_INTERPOLATION_FREQUENCY,
            False,
            "",
            "",
            None,
        )

    @pytest.fixture
    def api(self, config):
        mock = MagicMock()
        mock.config = config
        mock.send_device_command_action = AsyncMock()
        mock.send_device_command_properties = AsyncMock()
        yield mock

    @pytest.fixture
    def hass(self):
        hass = MagicMock(spec=HomeAssistant)
        hass.loop = MagicMock()
        hass.create_task.side_effect = lambda coro: (
            coro.close() if asyncio.iscoroutine(coro) else None
        )
        yield hass

    @pytest.fixture
    def entity(self, api, hass):
        light = OnyxLight(api, "UTC", "name", DeviceType.BASIC_LIGHT, "uuid")
        light.hass = hass
        yield light

    @pytest.fixture
    def dimmable_entity(self, api):
        yield OnyxLight(api, "UTC", "name", DeviceType.DIMMABLE_LIGHT, "uuid")

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
        assert ColorMode.ONOFF in entity.supported_color_modes
        assert api.device.called
        assert brightness_supported(entity.supported_color_modes) is False

    def test_color_mode_dimmable_light(self, api, dimmable_entity, device):
        device.device_type = DeviceType.DIMMABLE_LIGHT
        api.device.return_value = device
        assert dimmable_entity.color_mode == ColorMode.BRIGHTNESS
        assert len(dimmable_entity.supported_color_modes) == 1
        assert ColorMode.BRIGHTNESS in dimmable_entity.supported_color_modes
        assert api.device.called
        assert brightness_supported(dimmable_entity.supported_color_modes) is True

    def test_brightness(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.brightness == 25.5
        assert api.device.called

    def test_brightness_zero_max(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=0, read_only=False
        )
        api.device.return_value = device
        assert entity.brightness == 0

    @pytest.mark.asyncio
    async def test_async_turn_on_with_custom_max(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=0, minimum=0, maximum=500, read_only=False
        )
        api.device.return_value = device
        await entity.async_turn_on(brightness=255)
        api.send_device_command_properties.assert_called_once()
        args, _ = api.send_device_command_properties.call_args
        assert args[0] == "uuid"
        assert args[1]["target_brightness"] == 500

    @pytest.mark.asyncio
    async def test_async_turn_on_without_actual_brightness_fallback(
        self, api, entity, device
    ):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=255, read_only=False
        )
        api.device.return_value = device
        await entity.async_turn_on(brightness=128)
        api.send_device_command_properties.assert_called_once()
        args, _ = api.send_device_command_properties.call_args
        assert args[0] == "uuid"
        assert args[1]["target_brightness"] == 128

    def test_start_dim_device_no_keyframes(self, entity):
        animation = AnimationValue(start=0, current_value=0, keyframes=[])
        assert entity._start_dim_device(animation) is None

    def test_start_dim_device_all_none_keyframes(self, entity):
        animation = AnimationValue(start=0, current_value=0, keyframes=[None])
        assert entity._start_dim_device(animation) is None

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
        assert entity.brightness == 25.5

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

    def test_is_on_no_brightness(self, entity):
        with patch.object(
            type(entity),
            "_actual_brightness",
            new_callable=PropertyMock,
            return_value=None,
        ):
            assert entity.is_on is None

    @pytest.mark.asyncio
    async def test_turn_off(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        await entity.async_turn_off()
        api.send_device_command_action.assert_called_with("uuid", Action.LIGHT_OFF)

    @pytest.mark.asyncio
    async def test_turn_on(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        await entity.async_turn_on(brightness=10)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_brightness": 4,
                "dim_duration": 1928,
            },
        )
        assert api.device.called

    @pytest.mark.asyncio
    async def test_turn_on_no_brightness(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        await entity.async_turn_on()
        api.send_device_command_action.assert_called_with(
            "uuid",
            Action.LIGHT_ON,
        )
        assert not api.device.called

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

    def test__get_dim_duration(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=14645, maximum=65535, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(31) == 601
        assert api.device.called

    def test__get_dim_duration_custom_max(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=14645, maximum=65535, minimum=0, read_only=False
        )
        api.config.max_dim_duration = 1000
        api.device.return_value = device
        assert entity._get_dim_duration(31) == 378
        assert api.device.called

    def test__get_dim_duration_custom_min(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=14645, maximum=65535, minimum=0, read_only=False
        )
        api.config.min_dim_duration = 2000
        api.device.return_value = device
        assert entity._get_dim_duration(31) == 2000
        assert api.device.called

    def test__get_dim_duration_same(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(100) == DEFAULT_MIN_DIM_DURATION
        assert api.device.called

    def test__get_dim_duration_invalid_value(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=None, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(90) == 1820
        assert api.device.called

    def test__get_dim_duration_actual_lower_than_new(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=0, maximum=65535, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(65535) == DEFAULT_MAX_DIM_DURATION
        assert api.device.called

    def test__get_dim_duration_new_lower_than_actual(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=65535, maximum=65535, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(0) == DEFAULT_MAX_DIM_DURATION
        assert api.device.called

    def test__get_dim_duration_force_higher_than_max(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=65535, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(0) == DEFAULT_MAX_DIM_DURATION
        assert api.device.called

    def test_handle_coordinator_update(self, entity, device, api):
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
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            with patch.object(entity, "_start_dim_device") as mock_start_dim_device:
                entity._handle_coordinator_update()
                mock_start_dim_device.assert_called_with(animation)
                assert api.device.called
                assert mock_schedule_update_ha_state.called

    def test_handle_coordinator_update_no_animation(self, entity, device, api):
        animation = None
        device.actual_brightness = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        api.device.return_value = device
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            with patch.object(entity, "_start_dim_device") as mock_start_dim_device:
                entity._handle_coordinator_update()
                mock_start_dim_device.assert_not_called
                assert api.device.called
                assert mock_schedule_update_ha_state.called

    def test_start_dim_device_within_time(self, entity):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=1000,
                    delay=0,
                )
            ],
        )
        with patch.object(entity, "_end_dim_device") as mock_end_dim_device:
            entity._start_dim_device(animation)
            assert not mock_end_dim_device.called

    def test_start_dim_device_end(self, entity, api, config):
        current_time = time.time()
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
        with patch.object(entity, "_end_dim_device") as mock_end_dim_device:
            config.additional_delay = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_dim_device(animation)
            assert mock_end_dim_device.called
            assert config_mock.called

    def test_start_dim_device_end_within_time(self, entity, api, config):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=1000,
                    delay=0,
                )
            ],
        )
        with patch.object(entity, "_end_dim_device") as mock_end_dim_device:
            config.additional_delay = 1000
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_dim_device(animation)
            assert not mock_end_dim_device.called
            assert config_mock.called

    def test_start_dim_device_end_within_time_interpolation(self, entity, api, config):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=1000,
                    delay=0,
                )
            ],
        )
        with patch.object(entity, "_end_dim_device") as mock_end_dim_device:
            config.additional_delay = 1000
            config.interpolation_frequency = 500
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_dim_device(animation)
            assert not mock_end_dim_device.called
            assert config_mock.called

    def test_end_dim_device(self, api, entity, device):
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
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            entity._end_dim_device()
            assert api.device.called
            assert not mock_schedule_update_ha_state.called
            assert entity.hass.create_task.called
            api.send_device_command_action.assert_called_with("uuid", Action.STOP)

    def test_end_dim_device_within_time(self, api, entity, device):
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
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            entity._end_dim_device()
            assert api.device.called
            assert mock_schedule_update_ha_state.called
            assert not entity.hass.async_create_task.called
            assert entity._device.actual_brightness.value == 1

    def test_end_dim_device_within_time_using_delay(self, api, entity, device):
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
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            entity._end_dim_device()
            assert api.device.called
            assert not mock_schedule_update_ha_state.called
            assert not entity.hass.async_create_task.called

    # ------------------------------------------------------------------ #
    # Mutmut: async_turn_on — and guard for actual_brightness              #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_turn_on_brightness_and_guard_none_maximum(self, api, entity, device):
        """Mutmut: actual_brightness and actual_brightness.maximum vs ... or ...

        When actual_brightness exists but maximum is 0 (falsy), 'and' falls to
        default 255; 'or' would use actual_brightness.maximum (0) directly, making
        hella_brightness=0 for any input.
        Mock _get_dim_duration to isolate the target_max computation.
        """
        device.actual_brightness = NumericValue(
            value=0, maximum=0, minimum=0, read_only=False
        )
        api.device.return_value = device

        with patch.object(entity, "_get_dim_duration", return_value=1000):
            await entity.async_turn_on(brightness=255)

        # With 'and': target_max = 255 (default) → hella = ceil(255/255*255) = 255
        # With 'or':  target_max = 0 → ceil(255/255*0) = 0
        args, _ = api.send_device_command_properties.call_args
        assert args[1]["target_brightness"] == 255

    @pytest.mark.asyncio
    async def test_turn_on_brightness_with_valid_maximum(self, api, entity, device):
        """Mutmut: ensure actual_brightness.maximum is used when truthy."""
        device.actual_brightness = NumericValue(
            value=0, maximum=200, minimum=0, read_only=False
        )
        api.device.return_value = device

        with patch.object(entity, "_get_dim_duration", return_value=1000):
            await entity.async_turn_on(brightness=255)

        # target_max = 200; hella = ceil(255/255*200) = 200
        args, _ = api.send_device_command_properties.call_args
        assert args[1]["target_brightness"] == 200

    # ------------------------------------------------------------------ #
    # Mutmut: _start_dim_device — additional_delay arithmetic              #
    # ------------------------------------------------------------------ #

    def test_start_dim_device_additional_delay_is_added(self, entity, api, config):
        """Mutmut: + additional_delay/1000 vs - additional_delay/1000."""
        current_time = time.time()
        animation = AnimationValue(
            start=current_time - 5,
            current_value=0,
            keyframes=[
                AnimationKeyframe(interpolation="linear", value=0, duration=3, delay=0)
            ],
        )
        # Without extra delay: end_time = (now-5)+3 = now-2 → done
        # With 6000ms delay: end_time = now-5+3+6 = now+4 → still moving
        with patch.object(entity, "_end_dim_device") as mock_end:
            config.additional_delay = 6_000
            config.interpolation_frequency = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_dim_device(animation)
            assert not mock_end.called

    # ------------------------------------------------------------------ #
    # Mutmut: _end_dim_device — animation is not None and animation.keyframes
    # vs ... or ...                                                        #
    # ------------------------------------------------------------------ #

    def test_end_dim_device_none_animation_yields_empty_keyframes(
        self, api, entity, device
    ):
        """Mutmut: animation is not None or animation.keyframes (NoneType.keyframes crash)."""
        device.actual_brightness = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=None,
        )
        api.device.return_value = device

        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity.hass, "create_task"):
                # Must not raise AttributeError for None.keyframes
                entity._end_dim_device()

    # ------------------------------------------------------------------ #
    # Mutmut: _get_dim_duration — > vs >= for max_dim_duration             #
    # ------------------------------------------------------------------ #

    def test_get_dim_duration_at_max_returns_max(self, entity, api, device, config):
        """Mutmut: duration > max vs duration >= max.

        Use target much larger than brightness range so computed duration far exceeds
        max_dim_duration. Result must be capped at max_dim_duration.
        """
        device.actual_brightness = NumericValue(
            value=0, maximum=1, minimum=0, read_only=False
        )
        api.device.return_value = device

        config.min_dim_duration = 0
        config.max_dim_duration = 100
        config_mock = PropertyMock(return_value=config)
        type(api).config = config_mock

        # abs(10000 - 0) / 1 * (100 - 0) + 0 = 1_000_000 >> 100 → capped to 100
        result = entity._get_dim_duration(10000)
        assert result == 100

    def test_get_dim_duration_below_max_returns_computed(
        self, entity, api, device, config
    ):
        """Mutmut: ensure values strictly below max are not capped."""
        device.actual_brightness = NumericValue(
            value=0, maximum=1000, minimum=0, read_only=False
        )
        api.device.return_value = device

        config.min_dim_duration = 0
        config.max_dim_duration = 100000  # very high cap
        config_mock = PropertyMock(return_value=config)
        type(api).config = config_mock

        # abs(1 - 0) / 1000 * 100000 = 100 → well below cap
        result = entity._get_dim_duration(1)
        assert result < 100000
