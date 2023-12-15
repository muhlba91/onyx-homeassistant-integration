"""Test for the ONYX Shutter Entity."""
import time
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.cover import (
    CoverDeviceClass,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
)
from homeassistant.core import HomeAssistant
from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.cover import OnyxShutter
from custom_components.hella_onyx.enum.moving_state import MovingState


class TestOnyxShutter:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        hass = MagicMock(spec=HomeAssistant)
        hass.loop = MagicMock()
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
            SUPPORT_OPEN
            | SUPPORT_CLOSE
            | SUPPORT_STOP
            | SUPPORT_SET_POSITION
            | SUPPORT_SET_TILT_POSITION
        )

    def test_supported_features_without_tilt(self, rollershutter_entity):
        assert rollershutter_entity.supported_features == (
            SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
        )

    def test_current_cover_position(self, api, entity, device):
        device.actual_position = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.current_cover_position == 90
        assert api.device.called

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
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_called_with(animation)
                assert api.device.called
                assert mock_async_write_ha_state.called

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
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_called_with(animation)
                assert api.device.called
                assert mock_async_write_ha_state.called

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
        with patch.object(entity, "async_write_ha_state") as mock_async_write_ha_state:
            with patch.object(
                entity, "_start_moving_device"
            ) as mock_start_moving_device:
                entity._handle_coordinator_update()
                mock_start_moving_device.assert_not_called
                assert api.device.called
                assert mock_async_write_ha_state.called

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

    def test_start_moving_device_end(self, entity):
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
            entity._start_moving_device(animation)
            assert mock_end_moving_device.called

    def test_start_moving_device_within_time(self, entity):
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
            entity._start_moving_device(animation)
            assert not mock_end_moving_device.called

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

    @patch("asyncio.run_coroutine_threadsafe")
    def test_open_cover(self, mock_run_coroutine_threadsafe, api, entity, device):
        device.actual_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.drivetime_up = NumericValue(
            value=0, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            entity.open_cover()
            mock_set_state.assert_called_with(MovingState.OPENING)
        api.send_device_command_action.assert_called_with("uuid", Action.OPEN)
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_close_cover(self, mock_run_coroutine_threadsafe, api, entity, device):
        device.actual_position = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.drivetime_down = NumericValue(
            value=0, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            entity.close_cover()
            mock_set_state.assert_called_with(MovingState.CLOSING)
        api.send_device_command_action.assert_called_with("uuid", Action.CLOSE)
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_set_cover_position(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
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
            entity.set_cover_position(position=10)
            mock_calculate_and_set_state.assert_called_with(10, 90)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_position": 90,
                "target_angle": 30,
            },
        )
        assert api.device.called
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_stop_cover(self, mock_run_coroutine_threadsafe, api, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            entity.stop_cover()
            mock_set_state.assert_called_with(MovingState.STILL)
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)
        assert mock_run_coroutine_threadsafe.called

    def test_open_cover_tilt(self, entity):
        with pytest.raises(NotImplementedError):
            entity.open_cover_tilt()

    def test_close_cover_tilt(self, entity):
        with pytest.raises(NotImplementedError):
            entity.close_cover_tilt()

    @patch("asyncio.run_coroutine_threadsafe")
    def test_set_cover_tilt_position(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
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
            entity.set_cover_tilt_position(tilt_position=10)
            mock_calculate_and_set_state.assert_called_with(10, 9)
        api.send_device_command_properties.assert_called_with(
            "uuid", {"target_angle": 9}
        )
        assert api.device.called
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_stop_cover_tilt(self, mock_run_coroutine_threadsafe, api, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            entity.stop_cover_tilt()
            mock_set_state.assert_called_with(MovingState.STILL)
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)
        assert mock_run_coroutine_threadsafe.called

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
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert mock_stop_cover.called
                assert mock_async_write_ha_state.called

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
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_stop_cover.called
                assert mock_async_write_ha_state.called
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
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_stop_cover.called
                assert mock_async_write_ha_state.called
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
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_stop_cover.called
                assert mock_async_write_ha_state.called
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
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert api.device.called
                assert not mock_stop_cover.called
                assert mock_async_write_ha_state.called
                assert entity._device.actual_angle.value == 0

    def test__end_moving_device_still(self, entity):
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            with patch.object(
                entity, "async_write_ha_state"
            ) as mock_async_write_ha_state:
                entity._end_moving_device()
                assert not mock_stop_cover.called
                assert not mock_async_write_ha_state.called

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

    def test__calculate_state_CLOSING(self, entity, device, api):
        assert entity._calculate_state(100, 10) == MovingState.OPENING

    def test__calculate_state_OPENING(self, entity, device, api):
        assert entity._calculate_state(10, 100) == MovingState.CLOSING

    def test__calculate_state_STILL(self, entity, api):
        api.device.return_value = None
        assert entity._calculate_state(10, 10) == MovingState.STILL
        assert not api.device.called
