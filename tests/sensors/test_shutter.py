"""Test for the ONYX Shutter Entity."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.cover import OnyxShutter
from custom_components.hella_onyx.enum.moving_state import MovingState

from .helpers import NOW, animated, make_api, value

MODULE = "custom_components.hella_onyx.sensors"


class TestOnyxShutter:
    @pytest.fixture
    def api(self):
        yield make_api()

    @pytest.fixture
    def device(self, api):
        device = Shutter(
            "uuid",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
            target_position=value(10),
            target_angle=value(45, 360),
            actual_position=value(10),
            actual_angle=value(45, 360),
        )
        api.device.return_value = device
        yield device

    @pytest.fixture(autouse=True)
    def call_later(self):
        with (
            patch(f"{MODULE}.shutter.async_call_later") as call_later,
            patch(f"{MODULE}.onyx_entity.async_call_later"),
            patch(f"{MODULE}.onyx_entity.async_track_time_interval"),
        ):
            yield call_later

    def create(self, api, device_type=DeviceType.RAFFSTORE_90):
        entity = OnyxShutter(api, "UTC", "name", device_type, "uuid")
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        return entity

    @pytest.fixture
    def entity(self, api):
        yield self.create(api)

    def test_properties(self, entity):
        assert entity.icon == "mdi:window-shutter"
        assert entity.name == "name"
        assert entity.unique_id == "uuid/Shutter"
        assert entity.device_class == CoverDeviceClass.SHUTTER

    def test_supported_features(self, api, entity):
        base = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert entity.supported_features == base | CoverEntityFeature.SET_TILT_POSITION
        assert (
            self.create(api, DeviceType.RAFFSTORE_180).supported_features
            == base | CoverEntityFeature.SET_TILT_POSITION
        )
        assert self.create(api, DeviceType.ROLLERSHUTTER).supported_features == base

    def test_max_angle(self, api, entity):
        assert entity._max_angle == 90
        assert self.create(api, DeviceType.RAFFSTORE_180)._max_angle == 180
        assert self.create(api, DeviceType.AWNING)._max_angle == 100

    def test_position(self, entity, device):
        assert entity.current_cover_position == 90
        assert entity.current_cover_tilt_position == 50
        assert not entity.is_closed

    def test_position_rounding(self, entity, device):
        device.actual_position = value(29)
        device.actual_angle = value(58, 360)
        assert entity.current_cover_position == 71
        assert entity.current_cover_tilt_position == 64

    def test_position_clamped(self, entity, device):
        device.actual_position = value(120)
        device.actual_angle = value(-10)
        assert entity.current_cover_position == 0
        assert entity.current_cover_tilt_position == 0
        device.actual_position = value(-10)
        device.actual_angle = value(100)
        assert entity.current_cover_position == 100
        assert entity.current_cover_tilt_position == 100

    def test_position_unknown(self, api, entity, device):
        device.actual_position = value(10, 0)
        assert entity.current_cover_position is None
        assert entity.is_closed is None
        device.actual_position = None
        device.actual_angle = None
        assert entity.current_cover_position is None
        assert entity.current_cover_tilt_position is None
        assert entity.is_closed is None
        api.device.return_value = None
        assert entity.current_cover_position is None
        assert entity.current_cover_tilt_position is None
        assert entity.is_closed is None
        assert not entity.is_opening
        assert not entity.is_closing

    def test_is_closed_tolerance(self, entity, device):
        device.actual_position = value(97)
        assert entity.is_closed
        device.actual_position = value(96)
        assert not entity.is_closed

    def test_position_during_animation(self, entity, device):
        device.actual_position = animated(0, 100, NOW - 5, 10)
        assert entity.current_cover_position == 50
        assert entity.is_closing
        assert not entity.is_opening

    def test_position_after_natural_end(self, entity, device):
        # the device keeps reporting the start value after the animation ended
        device.actual_position = animated(0, 100, NOW - 100, 10)
        assert entity.current_cover_position == 0
        assert entity.is_closed
        assert not entity.is_closing

    def test_moving_within_additional_delay(self, entity, device):
        device.actual_position = animated(100, 0, NOW - 10.5, 10)
        assert entity.current_cover_position == 100
        assert entity.is_opening

    def test_tilt_animation(self, entity, device):
        device.actual_angle = animated(90, 0, NOW - 1, 2)
        assert entity.current_cover_tilt_position == 50
        assert entity.is_opening

    def test_animation_without_change(self, entity, device):
        device.actual_position = animated(50, 50, NOW, 10)
        assert not entity.is_opening
        assert not entity.is_closing

    def test_update_schedules_and_clears_request(self, entity, device, call_later):
        entity._set_requested_state(MovingState.CLOSING)
        unsub = entity._moving_timeout_unsub
        device.actual_position = animated(100, 0, NOW - 0.5, 10)
        with patch.object(entity, "_schedule_animation_updates") as schedule:
            entity._handle_coordinator_update()
            schedule.assert_called_once_with(
                [device.actual_position, device.actual_angle]
            )
        assert entity._requested_state == MovingState.STILL
        assert entity.is_opening
        unsub.assert_called_once_with()
        assert entity.async_write_ha_state.called

    def test_request_overrides_older_animation(self, entity, device):
        # moving down, then opened: the old animation is still running
        device.actual_position = animated(0, 100, NOW - 5, 10)
        entity._set_requested_state(MovingState.OPENING)
        entity._handle_coordinator_update()
        assert entity.is_opening
        assert entity._requested_state == MovingState.OPENING

    def test_update_without_animation_keeps_request(self, entity, device):
        entity._set_requested_state(MovingState.CLOSING)
        device.actual_position = animated(0, 100, NOW - 100, 10)
        entity._handle_coordinator_update()
        assert entity.is_closing

    async def test_open_close_stop(self, api, entity, device, call_later):
        await entity.async_open_cover()
        assert entity.is_opening
        assert entity.async_write_ha_state.called
        api.send_device_command_action.assert_called_with("uuid", Action.OPEN)
        assert call_later.call_args.args[1].total_seconds() == 180

        await entity.async_close_cover()
        assert entity.is_closing
        api.send_device_command_action.assert_called_with("uuid", Action.CLOSE)

        await entity.async_stop_cover()
        assert not entity.is_closing
        assert entity._moving_timeout_unsub is None
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)

        await entity.async_close_cover()
        await entity.async_stop_cover_tilt()
        assert not entity.is_closing
        api.send_device_command_action.assert_called_with("uuid", Action.STOP)

    async def test_set_position(self, api, entity, device):
        await entity.async_set_cover_position(**{ATTR_POSITION: 20})
        assert entity.is_closing
        assert entity.async_write_ha_state.called
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_position": 80, "target_angle": 45}
        )

    async def test_set_position_scaled(self, api, entity, device):
        device.target_position = value(10, 1000)
        device.target_angle = None
        await entity.async_set_cover_position(**{ATTR_POSITION: 30})
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_position": 700, "target_angle": 0}
        )

    async def test_set_position_unknown_device(self, api, entity):
        api.device.return_value = None
        await entity.async_set_cover_position(**{ATTR_POSITION: 50})
        assert not entity.is_opening
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_position": 50, "target_angle": 0}
        )

    async def test_set_position_without_value(self, api, entity):
        await entity.async_set_cover_position()
        await entity.async_set_cover_tilt_position()
        assert not api.send_device_command_properties.called

    async def test_set_tilt_position(self, api, entity, device):
        await entity.async_set_cover_tilt_position(**{ATTR_TILT_POSITION: 100})
        assert entity.is_closing
        api.send_device_command_properties.assert_called_once_with(
            "uuid", {"target_angle": 90}
        )

    async def test_failed_command_resets_state(self, api, entity, device):
        api.send_device_command_action.side_effect = RuntimeError
        with pytest.raises(RuntimeError):
            await entity.async_close_cover()
        assert not entity.is_closing
        assert entity._moving_timeout_unsub is None
        api.send_device_command_properties.side_effect = RuntimeError
        with pytest.raises(RuntimeError):
            await entity.async_set_cover_tilt_position(**{ATTR_TILT_POSITION: 0})
        assert not entity.is_opening

    async def test_open_close_tilt_not_supported(self, entity):
        with pytest.raises(NotImplementedError):
            await entity.async_open_cover_tilt()
        with pytest.raises(NotImplementedError):
            await entity.async_close_cover_tilt()

    def test_moving_timeout(self, entity, device, call_later):
        entity._set_requested_state(MovingState.CLOSING)
        assert call_later.call_args.args[0] is entity.hass
        assert call_later.call_args.args[2] == entity._handle_moving_timeout
        entity._handle_moving_timeout()
        assert not entity.is_closing
        assert entity._moving_timeout_unsub is None
        assert entity.async_write_ha_state.called

    async def test_will_remove_cancels_timeout(self, entity):
        entity._set_requested_state(MovingState.CLOSING)
        unsub = entity._moving_timeout_unsub
        await entity.async_will_remove_from_hass()
        unsub.assert_called_once_with()
        assert entity._moving_timeout_unsub is None

    def test_calculate_state(self):
        assert OnyxShutter._calculate_state(10, 5) == MovingState.OPENING
        assert OnyxShutter._calculate_state(5, 10) == MovingState.CLOSING
        assert OnyxShutter._calculate_state(5, 5) == MovingState.STILL
        assert OnyxShutter._calculate_state(None, 5) == MovingState.STILL
