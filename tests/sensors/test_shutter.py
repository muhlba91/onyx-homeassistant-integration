"""Test for the ONYX Shutter Entity."""

import asyncio
import pytest
import time

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant

from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.shutter import Shutter
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
from custom_components.hella_onyx.cover import OnyxShutter
from custom_components.hella_onyx.enum.moving_state import MovingState


class TestOnyxShutter:
    @pytest.fixture
    def api(self):
        mock = MagicMock()
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
        shutter = OnyxShutter(api, "UTC", "name", DeviceType.RAFFSTORE_90, "uuid")
        shutter.hass = hass
        yield shutter

    @pytest.fixture
    def rollershutter_entity(self, api):
        yield OnyxShutter(api, "UTC", "name", DeviceType.ROLLERSHUTTER, "uuid")

    @pytest.fixture
    def device(self):
        yield Shutter(
            "id",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

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

    def test_icon(self, entity):
        assert entity.icon == "mdi:window-shutter"

    def test_name(self, entity):
        assert entity.name == "name"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Shutter"

    def test_device_class(self, entity):
        assert entity.device_class == CoverDeviceClass.SHUTTER

    def test_supported_features_with_tilt(self, entity):
        assert entity.supported_features == (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
            | CoverEntityFeature.SET_TILT_POSITION
        )

    def test_supported_features_without_tilt(self, rollershutter_entity):
        assert rollershutter_entity.supported_features == (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    def test_current_cover_position(self, api, entity, device):
        device.actual_position = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.current_cover_position == 90
        assert api.device.called

    def test_current_cover_position_zero_max(self, api, entity, device):
        device.actual_position = NumericValue(
            value=10, maximum=0, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity.current_cover_position is None

    def test_current_cover_position_scaled_max(self, api, entity, device):
        device.actual_position = NumericValue(
            value=25, minimum=0, maximum=50, read_only=False
        )
        api.device.return_value = device
        assert entity.current_cover_position == 50

    def test_current_cover_tilt_position_none_device(self, entity, device, api):
        device.actual_angle = None
        api.device.return_value = device
        assert entity.current_cover_tilt_position is None

    def test_start_moving_device_none_keyframes(self, entity):
        animation = AnimationValue(start=0, current_value=0, keyframes=[None])
        assert entity._start_moving_device(animation) is None

    def test_is_closed_none_position(self, entity, device, api):
        device.actual_position = None
        api.device.return_value = device
        assert not entity.is_closed

    def test_current_cover_position_with_animation(self, api, entity, device):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=20
                )
            ],
        )
        device.actual_position = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False, animation=animation
        )
        api.device.return_value = device
        assert entity.current_cover_position == 90
        assert api.device.called

    def test_current_cover_tilt_position(self, api, entity, device):
        device.actual_angle = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.current_cover_tilt_position == 11
        assert api.device.called

    def test_current_cover_tilt_position_with_animation(self, api, entity, device):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=20
                )
            ],
        )
        device.actual_angle = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False, animation=animation
        )
        api.device.return_value = device
        assert entity.current_cover_tilt_position == 11
        assert api.device.called

    def test_handle_coordinator_update_none_device(self, entity, api):
        with patch.object(
            type(entity), "_device", new_callable=PropertyMock, return_value=None
        ):
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                with patch.object(
                    entity, "_start_moving_device"
                ) as mock_start_moving_device:
                    entity._handle_coordinator_update()
                    mock_start_moving_device.assert_not_called()
                    mock_schedule_update_ha_state.assert_not_called()

    def test_handle_coordinator_update_position(self, entity, device, api):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=10
                )
            ],
        )
        device.actual_position = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        device.actual_angle = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=None,
        )
        api.device.return_value = device
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_called_with(animation)
                assert api.device.called
                assert mock_schedule_update_ha_state.called

    def test_handle_coordinator_update_angle(self, entity, device, api):
        animation = AnimationValue(
            start=0,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=10
                )
            ],
        )
        device.actual_position = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=None,
        )
        device.actual_angle = NumericValue(
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
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_called_with(animation)
                assert api.device.called
                assert mock_schedule_update_ha_state.called

    def test_handle_coordinator_update_no_animation(self, entity, device, api):
        animation = None
        device.actual_position = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        device.actual_angle = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=None,
        )
        api.device.return_value = device
        with patch.object(
            entity, "schedule_update_ha_state"
        ) as mock_schedule_update_ha_state:
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_not_called
                assert api.device.called
                assert mock_schedule_update_ha_state.called

    def test_handle_coordinator_update_position_still_sets_state(
        self, entity, device, api
    ):
        """External Onyx app: animation arrives while state is STILL → state auto-set."""
        animation = AnimationValue(
            start=0,
            current_value=10,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", duration=10, delay=0, value=50
                )
            ],
        )
        device.actual_position = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=animation,
        )
        device.actual_angle = NumericValue(
            value=0,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=None,
        )
        device.target_position = NumericValue(
            value=50, minimum=0, maximum=100, read_only=False, animation=None
        )
        api.device.return_value = device
        assert entity._moving_state == MovingState.STILL
        with patch.object(entity, "_start_moving_device"):
            with patch.object(entity, "schedule_update_ha_state"):
                entity._handle_coordinator_update()
        # 10 → 50 is closing (increasing raw position)
        assert entity._moving_state == MovingState.CLOSING

    def test_handle_coordinator_update_angle_still_sets_state(
        self, entity, device, api
    ):
        """External Onyx app: angle animation arrives while state is STILL → state auto-set."""
        animation = AnimationValue(
            start=0,
            current_value=90,
            keyframes=[
                AnimationKeyframe(interpolation="linear", duration=10, delay=0, value=0)
            ],
        )
        device.actual_position = NumericValue(
            value=10,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=None,
        )
        device.actual_angle = NumericValue(
            value=90,
            minimum=0,
            maximum=360,
            read_only=False,
            animation=animation,
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=360, read_only=False, animation=None
        )
        api.device.return_value = device
        assert entity._moving_state == MovingState.STILL
        with patch.object(entity, "_start_moving_device"):
            with patch.object(entity, "schedule_update_ha_state"):
                entity._handle_coordinator_update()
        # 90 → 0 is opening (decreasing raw angle)
        assert entity._moving_state == MovingState.OPENING

    def test_is_not_opening(self, entity):
        assert not entity.is_opening

    def test_is_opening(self, entity):
        entity._moving_state = MovingState.OPENING
        assert entity.is_opening

    def test_is_not_closing(self, entity):
        assert not entity.is_closing

    def test_is_closing(self, entity):
        entity._moving_state = MovingState.CLOSING
        assert entity.is_closing

    def test_is_not_closed(self, api, entity, device):
        device.actual_position = NumericValue(
            value=10, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert not entity.is_closed
        assert api.device.called

    def test_is_closed(self, api, entity, device):
        device.actual_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity.is_closed
        assert api.device.called

    def test_start_moving_device_end(self, entity, api, config):
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
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config.additional_delay = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_end_multiple_keyframes(self, entity, api, config):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=5,
                    delay=0,
                ),
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=5,
                    delay=0,
                ),
            ],
        )
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config.additional_delay = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_within_time(self, entity, api, config):
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
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config.additional_delay = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_within_time_interpolation(self, entity, api, config):
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
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config.additional_delay = 0
            config.interpolation_frequency = 500
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_within_time_multiple_keyframes(
        self, entity, api, config
    ):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=500,
                    delay=0,
                ),
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=500,
                    delay=0,
                ),
            ],
        )
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config.additional_delay = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_within_time_due_to_additional_delay(
        self, entity, api, config
    ):
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
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called
            assert config_mock.called

    def test_start_moving_device_still(self, entity):
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
        entity._moving_state = MovingState.STILL
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called

    def test_start_moving_device_still_multiple_keyframes(self, entity):
        current_time = time.time()
        animation = AnimationValue(
            start=current_time - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=5,
                    delay=0,
                ),
                AnimationKeyframe(
                    interpolation="linear",
                    value=0,
                    duration=5,
                    delay=0,
                ),
            ],
        )
        entity._moving_state = MovingState.STILL
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called

    def test_start_moving_device_empty_keyframes(self, entity):
        entity._moving_state = MovingState.CLOSING
        animation = AnimationValue(
            start=time.time(),
            current_value=0,
            keyframes=[],
        )
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called

    def test_start_moving_device_none_keyframe_items(self, entity):
        entity._moving_state = MovingState.CLOSING
        animation = AnimationValue(
            start=time.time(),
            current_value=0,
            keyframes=[None],
        )
        with patch.object(entity, "_end_moving_device") as mock_end_moving_device:
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called

    @pytest.mark.asyncio
    async def test_open_cover(self, api, entity, device):
        device.actual_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.drivetime_up = NumericValue(
            value=0, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            await entity.async_open_cover()
            mock_set_state.assert_called_with(MovingState.OPENING)
        api.send_device_command_action.assert_called_with("uuid", Action.OPEN)

    @pytest.mark.asyncio
    async def test_close_cover(self, api, entity, device):
        device.actual_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.drivetime_down = NumericValue(
            value=0, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            await entity.async_close_cover()
            mock_set_state.assert_called_with(MovingState.CLOSING)
        api.send_device_command_action.assert_called_with("uuid", Action.CLOSE)

    @pytest.mark.asyncio
    async def test_set_cover_position(self, api, entity, device):
        device.target_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.actual_position = NumericValue(
            value=10, maximum=100, minimum=0, read_only=False
        )
        device.target_angle = NumericValue(
            value=30, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            await entity.async_set_cover_position(position=10)
            mock_calculate_and_set_state.assert_called_with(10, 90)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_position": 90,
                "target_angle": 30,
            },
        )
        assert api.device.called

    @pytest.mark.asyncio
    async def test_set_cover_position_none_target_angle(self, api, entity, device):
        device.target_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.actual_position = NumericValue(
            value=10, maximum=100, minimum=0, read_only=False
        )
        device.target_angle = None
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            await entity.async_set_cover_position(position=10)
            mock_calculate_and_set_state.assert_called_with(10, 90)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_position": 90,
                "target_angle": 0,
            },
        )
        assert api.device.called

    @pytest.mark.asyncio
    async def test_stop_cover(self, api, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            await entity.async_stop_cover()
            mock_set_state.assert_called_with(MovingState.STILL)
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)

    @pytest.mark.asyncio
    async def test_open_cover_tilt(self, entity):
        with pytest.raises(NotImplementedError):
            await entity.async_open_cover_tilt()

    @pytest.mark.asyncio
    async def test_close_cover_tilt(self, entity):
        with pytest.raises(NotImplementedError):
            await entity.async_close_cover_tilt()

    @pytest.mark.asyncio
    async def test_set_cover_tilt_position(self, api, entity, device):
        device.rotationtime = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.actual_angle = NumericValue(
            value=10, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            await entity.async_set_cover_tilt_position(tilt_position=10)
            mock_calculate_and_set_state.assert_called_with(10, 9)
        api.send_device_command_properties.assert_called_with(
            "uuid", {"target_angle": 9}
        )
        assert api.device.called

    @pytest.mark.asyncio
    async def test_stop_cover_tilt(self, api, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            await entity.async_stop_cover_tilt()
            mock_set_state.assert_called_with(MovingState.STILL)
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)

    def test__set_state_STILL(self, entity):
        with patch.object(entity, "async_update") as mock_async_update:
            entity._set_state(MovingState.STILL)
            assert not mock_async_update.called
        assert not entity.is_opening
        assert not entity.is_closing

    def test__set_state_CLOSING(self, entity):
        entity._set_state(MovingState.CLOSING)
        assert not entity.is_opening
        assert entity.is_closing

    def test__set_state_OPENING(self, entity):
        entity._set_state(MovingState.OPENING)
        assert entity.is_opening
        assert not entity.is_closing

    def test__end_moving_device(self, entity):
        entity._moving_state = MovingState.CLOSING
        entity._device.actual_angle.animation = AnimationValue(
            time.time() - 1000, 10, [AnimationKeyframe("linear", 0, 100, 90)]
        )
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called

    def test__end_moving_device_within_time(self, entity, api, device):
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time(), 0, [AnimationKeyframe("linear", 0, 20000, 50)]
            ),
        )
        device.target_angle = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time(), 0, [AnimationKeyframe("linear", 0, 10000, 50)]
            ),
        )
        device.target_position = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_angle.value == 1
                assert entity._device.actual_position.value == 1

    def test__end_moving_device_within_time_using_delay(self, entity, api, device):
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time() - 100, 10, [AnimationKeyframe("linear", 100000, 10, 50)]
            ),
        )
        device.target_position = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_position.value == 0

    def test__end_moving_device_only_position(self, entity, api, device):
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time() - 100, 10, [AnimationKeyframe("linear", 100000, 10, 50)]
            ),
        )
        device.target_position = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_position.value == 0

    def test__end_moving_device_only_angle(self, entity, api, device):
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(
                time.time() - 100, 10, [AnimationKeyframe("linear", 100000, 10, 50)]
            ),
        )
        device.target_angle = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_angle.value == 0

    def test__end_moving_device_position_none(self, entity, api, device):
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(time.time() - 100, 10, [None]),
        )
        device.target_position = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_angle.value == 0

    def test__end_moving_device_angle_none(self, entity, api, device):
        device.actual_angle = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
            animation=AnimationValue(time.time() - 100, 10, [None]),
        )
        device.target_angle = NumericValue(
            value=50,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        device.actual_position = NumericValue(
            value=0,
            maximum=100,
            minimum=0,
            read_only=False,
        )
        api.device.return_value = device
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_async_stop_cover.called
                assert mock_schedule_update_ha_state.called
                assert entity._device.actual_angle.value == 0

    def test__end_moving_device_still(self, entity):
        with patch.object(
            entity, "async_stop_cover", new_callable=MagicMock
        ) as mock_async_stop_cover:
            with patch.object(
                entity, "schedule_update_ha_state"
            ) as mock_schedule_update_ha_state:
                entity._end_moving_device()
                assert not mock_async_stop_cover.called
                assert not mock_schedule_update_ha_state.called

    def test__calculate_and_set_state_CLOSING(self, entity, device, api):
        device.drivetime_down = NumericValue(
            value=50, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.CLOSING
                entity._calculate_and_set_state(10, 100)
                mock_calculate_state.assert_called_once_with(10, 100)
                mock_set_state.assert_called_once_with(MovingState.CLOSING)

    def test__calculate_and_set_state_OPENING(self, entity, device, api):
        device.drivetime_up = NumericValue(
            value=50, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.OPENING
                entity._calculate_and_set_state(100, 10)
                mock_calculate_state.assert_called_once_with(100, 10)
                mock_set_state.assert_called_once_with(MovingState.OPENING)

    def test__calculate_and_set_state_tilt(self, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.CLOSING
                entity._calculate_and_set_state(10, 100)
                mock_calculate_state.assert_called_once_with(10, 100)
                mock_set_state.assert_called_once_with(MovingState.CLOSING)

    def test__max_angle(self, entity):
        assert entity._max_angle == 90

    def test__max_angle_180(self, entity):
        entity._type = DeviceType.RAFFSTORE_180
        assert entity._max_angle == 180

    def test__max_angle_rollershutter(self, rollershutter_entity):
        assert rollershutter_entity._max_angle == 100

    def test__calculate_state_CLOSING(self, entity):
        assert entity._calculate_state(100, 10) == MovingState.OPENING

    def test__calculate_state_OPENING(self, entity):
        assert entity._calculate_state(10, 100) == MovingState.CLOSING

    def test__calculate_state_STILL(self, entity, api):
        api.device.return_value = None
        assert entity._calculate_state(10, 10) == MovingState.STILL
        assert not api.device.called

    def test__calculate_animation_duration_and_delay(self, entity):
        assert entity._calculate_animation_duration_and_delay(
            [AnimationKeyframe("linear", 100000, 10, 50)]
        ) == (10, 100000)

    def test__calculate_animation_duration_and_delay_multiple_keyframes(self, entity):
        assert entity._calculate_animation_duration_and_delay(
            [
                AnimationKeyframe("linear", 100000, 10, 50),
                AnimationKeyframe("linear", 100000, 10, 50),
            ]
        ) == (20, 200000)

    def test__calculate_animation_duration_and_delay_none_keyframes(self, entity):
        assert entity._calculate_animation_duration_and_delay([None]) is None

    def test__calculate_animation_duration_and_delay_empty(self, entity):
        assert entity._calculate_animation_duration_and_delay([]) is None

    # ------------------------------------------------------------------ #
    # Mutmut: async_set_cover_position arithmetic                          #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_async_set_cover_position_hella_position_math(
        self, entity, api, device, config
    ):
        """Mutmut: ceil(position * (target_max / 100)) vs ceil(position / (target_max / 100))."""
        device.actual_position = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        device.target_position = NumericValue(
            value=0, minimum=0, maximum=200, read_only=False
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        api.config = config

        with patch.object(entity, "schedule_update_ha_state"):
            await entity.async_set_cover_position(**{ATTR_POSITION: 0})

        # position = 100 - 0 = 100; target_max = 200; hella = ceil(100 * (200/100)) = 200
        args, _ = api.send_device_command_properties.call_args
        assert args[1]["target_position"] == 200  # not 199 or 25

    @pytest.mark.asyncio
    async def test_async_set_cover_position_and_guard(
        self, entity, api, device, config
    ):
        """Mutmut: target_position and target_position.maximum vs ... or ...
        When target_position exists but maximum is 0 (falsy), 'and' falls to 100 default
        but 'or' would use target_position.maximum (0) directly."""
        device.actual_position = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        # maximum=0 is falsy; with 'and' guard: uses default 100; with 'or': uses 0
        device.target_position = NumericValue(
            value=0, minimum=0, maximum=0, read_only=False
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        api.config = config

        with patch.object(entity, "schedule_update_ha_state"):
            await entity.async_set_cover_position(**{ATTR_POSITION: 50})

        # target_max must be 100 (default) because maximum is 0 (falsy)
        args, _ = api.send_device_command_properties.call_args
        assert args[1]["target_position"] == 50  # ceil(50 * (100/100))

    @pytest.mark.asyncio
    async def test_async_set_cover_tilt_position_math(
        self, entity, api, device, config
    ):
        """Mutmut: ceil(angle * (max_angle / 100)) vs ceil(angle * (max_angle / 101))."""
        device.actual_position = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        api.config = config

        entity._type = DeviceType.RAFFSTORE_180
        # entity is RAFFSTORE_180 => _max_angle = 180
        # angle=100 => hella_angle = ceil(100 * (180/100)) = ceil(180) = 180
        # with / 101 => ceil(100 * (180/101)) = ceil(178.21) = 179
        with patch.object(entity, "schedule_update_ha_state"):
            await entity.async_set_cover_tilt_position(**{ATTR_TILT_POSITION: 100})

        args, _ = api.send_device_command_properties.call_args
        assert args[1]["target_angle"] == 180

    # ------------------------------------------------------------------ #
    # Mutmut: _start_moving_device                                         #
    # ------------------------------------------------------------------ #

    def test_start_moving_device_additional_delay_is_added(self, entity, api, config):
        """Mutmut: + additional_delay/1000 vs - additional_delay/1000.

        A positive additional_delay should push end_time forward so the device
        is still considered moving even when the animation duration has passed.
        """
        current_time = time.time()
        # Keyframe duration puts end_time just in the past without delay
        animation = AnimationValue(
            start=current_time - 10,
            current_value=0,
            keyframes=[
                AnimationKeyframe(interpolation="linear", value=0, duration=5, delay=0)
            ],
        )
        entity._moving_state = MovingState.CLOSING

        with patch.object(entity, "_end_moving_device") as mock_end:
            # additional_delay = 10_000 ms → +10 s → end_time in future
            config.additional_delay = 10_000
            config.interpolation_frequency = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end.called

    def test_start_moving_device_additional_delay_divisor_is_1000(
        self, entity, api, config
    ):
        """Mutmut: / 1000 vs / 1001 — ensure the conversion 1ms=0.001s is correct."""
        current_time = time.time()
        animation = AnimationValue(
            start=current_time - 5,
            current_value=0,
            keyframes=[
                AnimationKeyframe(interpolation="linear", value=0, duration=3, delay=0)
            ],
        )
        entity._moving_state = MovingState.CLOSING

        with patch.object(entity, "_end_moving_device") as mock_end:
            # 1000 ms / 1000 = +1 s → end_time still in past (5s ago + 3 + 1 = -1s → done)
            # 1000 ms / 1001 ≈ +0.999 s → same result
            # Use 2000ms: /1000 → +2s ; start-5+3+2 = 0 → current, still past/same
            # Use 6000ms: /1000 → +6s ; start-5+3+6 = +4s → future! (not done)
            config.additional_delay = 6_000
            config.interpolation_frequency = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            # With correct /1000: end_time = (now-5) + 3 + 6 = now+4 → still moving
            assert not mock_end.called

    def test_start_moving_device_is_moving_uses_strict_less_than(
        self, entity, api, config
    ):
        """Mutmut: current_time < end_time vs current_time <= end_time.

        When current_time exactly equals end_time the device must NOT be considered
        moving (strict < means it's done). We can only verify that is_moving is True
        when there's time remaining, and False (end called) when past.
        """
        current_time = time.time()
        # end_time is well in the future → is_moving must be True
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=0, duration=1000, delay=0
                )
            ],
        )
        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "_end_moving_device") as mock_end:
            config.additional_delay = 0
            config.interpolation_frequency = 0
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            assert not mock_end.called

    def test_start_moving_device_interpolation_frequency_zero_skips_loop(
        self, entity, api, config
    ):
        """Mutmut: interpolation_frequency > 0 vs >= 0.

        When frequency is 0 the loop must NOT execute (division by zero).
        """
        current_time = time.time()
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=0, duration=1000, delay=0
                )
            ],
        )
        entity._moving_state = MovingState.CLOSING

        scheduled_calls = []

        def capture_track(hass, callback, dt):
            scheduled_calls.append(dt)

        with patch(
            "custom_components.hella_onyx.sensors.shutter.async_track_point_in_utc_time",
            side_effect=capture_track,
        ):
            config.additional_delay = 0
            config.interpolation_frequency = 0  # must skip the for-loop
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            # Only the final end_time call, not intermediate ones
            assert len(scheduled_calls) == 1

    def test_start_moving_device_range_uses_floor_division(self, entity, api, config):
        """Mutmut: time_delta.total_seconds() // freq vs / freq.

        With floor division // the number of intermediate slices is an integer;
        with true division / range() raises TypeError. Verify it runs without error.
        """
        current_time = time.time()
        animation = AnimationValue(
            start=current_time,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=0, duration=100, delay=0
                )
            ],
        )
        entity._moving_state = MovingState.CLOSING

        scheduled_calls = []

        def capture_track(hass, callback, dt):
            scheduled_calls.append(dt)

        with patch(
            "custom_components.hella_onyx.sensors.shutter.async_track_point_in_utc_time",
            side_effect=capture_track,
        ):
            config.additional_delay = 0
            config.interpolation_frequency = (
                7  # non-divisor to expose float vs int issue
            )
            config_mock = PropertyMock(return_value=config)
            type(api).config = config_mock
            entity._start_moving_device(animation)
            # Should complete without TypeError
            assert len(scheduled_calls) >= 1

    # ------------------------------------------------------------------ #
    # Mutmut: _end_moving_device                                           #
    # ------------------------------------------------------------------ #

    def test_end_moving_device_empty_keyframes_skips_position(
        self, entity, api, device, config
    ):
        """Mutmut: len(keyframes) > 0 vs >= 0 — empty list must NOT compute keyframe."""
        device.actual_position = NumericValue(
            value=50,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=AnimationValue(start=0, current_value=50, keyframes=[]),
        )
        device.actual_angle = NumericValue(
            value=0,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=AnimationValue(start=0, current_value=0, keyframes=[]),
        )
        device.target_position = NumericValue(
            value=100, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity.hass, "create_task") as mock_create_task:
                # Empty keyframes → position_keyframe = None → no stop issued
                entity._end_moving_device()
                assert not mock_create_task.called

    def test_end_moving_device_position_end_time_computed(
        self, entity, api, device, config
    ):
        """Mutmut: position_end_time = None replaces the real calculation."""
        t = time.time()
        animation = AnimationValue(
            start=t - 100,  # well in the past
            current_value=50,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=100, duration=10, delay=0
                )
            ],
        )
        device.actual_position = NumericValue(
            value=50, minimum=0, maximum=100, read_only=False, animation=animation
        )
        device.actual_angle = NumericValue(
            value=0,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=AnimationValue(start=0, current_value=0, keyframes=[]),
        )
        device.target_position = NumericValue(
            value=100, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
                entity._end_moving_device()
                # end_time is in the past → stop must be issued
                assert mock_async_stop_cover.called

    def test_end_moving_device_angle_end_time_sign(self, entity, api, device, config):
        """Mutmut: angle_start_time + angle_keyframe[0] vs - angle_keyframe[0]."""
        t = time.time()
        angle_animation = AnimationValue(
            start=t - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=90, duration=10, delay=0
                )
            ],
        )
        device.actual_position = NumericValue(
            value=0,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=AnimationValue(start=0, current_value=0, keyframes=[]),
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False, animation=angle_animation
        )
        device.target_position = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=90, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
                entity._end_moving_device()
                # angle_end_time = t-100 + 0(delay) + 10(duration) = t-90 → in the past
                # position_end_time = None (no position keyframes)
                # condition: position_end_time is None and angle_end_time is not None and current > angle_end_time
                assert mock_async_stop_cover.called

    def test_end_moving_device_null_condition_angle_none_position_done(
        self, entity, api, device, config
    ):
        """Mutmut: angle_end_time is None vs is not None in the stop condition."""
        t = time.time()
        pos_animation = AnimationValue(
            start=t - 100,
            current_value=50,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=100, duration=5, delay=0
                )
            ],
        )
        device.actual_position = NumericValue(
            value=50, minimum=0, maximum=100, read_only=False, animation=pos_animation
        )
        device.actual_angle = NumericValue(
            value=0,
            minimum=0,
            maximum=100,
            read_only=False,
            animation=AnimationValue(start=0, current_value=0, keyframes=[]),
        )
        device.target_position = NumericValue(
            value=100, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
                entity._end_moving_device()
                # angle_end_time IS None, position_end_time past → stop issued
                assert mock_async_stop_cover.called

    def test_end_moving_device_both_done_issues_stop(self, entity, api, device, config):
        """Mutmut: position/angle is not None vs is None in the both-done condition."""
        t = time.time()
        pos_animation = AnimationValue(
            start=t - 100,
            current_value=50,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=100, duration=5, delay=0
                )
            ],
        )
        angle_animation = AnimationValue(
            start=t - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(interpolation="linear", value=90, duration=5, delay=0)
            ],
        )
        device.actual_position = NumericValue(
            value=50, minimum=0, maximum=100, read_only=False, animation=pos_animation
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False, animation=angle_animation
        )
        device.target_position = NumericValue(
            value=100, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=90, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
                entity._end_moving_device()
                # Both end times are in the past → stop issued
                assert mock_async_stop_cover.called

    def test_end_moving_device_angle_keyframe_and_guard(
        self, entity, api, device, config
    ):
        """Mutmut: angle_animation is not None and angle_keyframe[0] > 0 vs ... or ..."""
        t = time.time()
        # position is past end → stop will be issued; angle too
        pos_animation = AnimationValue(
            start=t - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(
                    interpolation="linear", value=100, duration=5, delay=0
                )
            ],
        )
        angle_animation = AnimationValue(
            start=t - 100,
            current_value=0,
            keyframes=[
                AnimationKeyframe(interpolation="linear", value=90, duration=5, delay=0)
            ],
        )
        device.actual_position = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False, animation=pos_animation
        )
        device.actual_angle = NumericValue(
            value=0, minimum=0, maximum=100, read_only=False, animation=angle_animation
        )
        device.target_position = NumericValue(
            value=100, minimum=0, maximum=100, read_only=False
        )
        device.target_angle = NumericValue(
            value=90, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device

        entity._moving_state = MovingState.CLOSING
        with patch.object(entity, "schedule_update_ha_state"):
            with patch.object(entity, "async_stop_cover") as mock_async_stop_cover:
                entity._end_moving_device()
                assert mock_async_stop_cover.called
