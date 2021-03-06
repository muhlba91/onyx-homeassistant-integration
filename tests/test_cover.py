"""Test for the ONYX Shutter Entity."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.cover import (
    DEVICE_CLASS_SHUTTER,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from onyx_client.data.boolean_value import BooleanValue
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN, ONYX_API, ONYX_COORDINATOR
from custom_components.hella_onyx.cover import OnyxShutter, async_setup_entry
from custom_components.hella_onyx.moving_state import MovingState


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass):
    config_entry = ConfigEntry(1, DOMAIN, "entry", {}, "source", "POLL", {})

    class AsyncAddEntries:
        def __init__(self):
            self.called_async_add_entities = False

        def call(self, shutters, boolean):
            self.called_async_add_entities = True

    async_add_entries = AsyncAddEntries()

    mock_hass.data.return_value = {
        DOMAIN: {"entry_id": {ONYX_API: None, ONYX_COORDINATOR: None}}
    }

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities


class TestOnyxShutter:
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
        shutter = OnyxShutter(api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid")
        shutter.hass = hass
        yield shutter

    @pytest.fixture
    def rollershutter_entity(self, api, coordinator):
        yield OnyxShutter(api, coordinator, "name", DeviceType.ROLLERSHUTTER, "uuid")

    @pytest.fixture
    def device(self):
        yield Shutter(
            "id",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

    def test_name(self, entity):
        assert entity.name == "name"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Shutter"

    def test_device_class(self, entity):
        assert entity.device_class == DEVICE_CLASS_SHUTTER

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
        device.switch_drive_direction = BooleanValue(value=False, read_only=False)
        api.device.return_value = device
        assert entity.current_cover_position == 90
        assert api.device.called

    def test_current_cover_position_switched_drive_direction(self, api, entity, device):
        device.actual_position = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        device.switch_drive_direction = BooleanValue(value=True, read_only=False)
        api.device.return_value = device
        assert entity.current_cover_position == 10
        assert api.device.called

    def test_current_cover_tilt_position(self, api, entity, device):
        device.actual_angle = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        device.switch_drive_direction = BooleanValue(value=False, read_only=False)
        api.device.return_value = device
        assert entity.current_cover_tilt_position == 88
        assert api.device.called

    def test_current_cover_tilt_position_switched_drive_direction(
        self, api, entity, device
    ):
        device.actual_angle = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        device.switch_drive_direction = BooleanValue(value=True, read_only=False)
        api.device.return_value = device
        assert entity.current_cover_tilt_position == 11
        assert api.device.called

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
            mock_set_state.assert_called_with(
                MovingState.OPENING, delta=100, max_timedelta=0
            )
        api.send_device_command_action.assert_called_with("uuid", Action.OPEN)
        assert api.device.called
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
            mock_set_state.assert_called_with(
                MovingState.CLOSING, delta=0, max_timedelta=0
            )
        api.send_device_command_action.assert_called_with("uuid", Action.CLOSE)
        assert api.device.called
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
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            entity.set_cover_position(position=10)
            mock_calculate_and_set_state.assert_called_with(10, 90, -1)
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
    def test_set_cover_position_switched_drive_direction(
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
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            entity.set_cover_position(position=10)
            mock_calculate_and_set_state.assert_called_with(10, 10, -1)
        api.send_device_command_properties.assert_called_with(
            "uuid",
            {
                "target_position": 10,
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
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            entity.set_cover_tilt_position(tilt_position=10)
            mock_calculate_and_set_state.assert_called_with(10, 81, 100)
        api.send_device_command_properties.assert_called_with(
            "uuid", {"target_angle": 81}
        )
        assert api.device.called
        assert mock_run_coroutine_threadsafe.called

    @patch("asyncio.run_coroutine_threadsafe")
    def test_set_cover_tilt_position_switched_drive_direction(
        self, mock_run_coroutine_threadsafe, api, entity, device
    ):
        device.rotationtime = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        device.actual_angle = NumericValue(
            value=10, maximum=100, minimum=0, read_only=False
        )
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        with patch.object(
            entity, "_calculate_and_set_state"
        ) as mock_calculate_and_set_state:
            entity.set_cover_tilt_position(tilt_position=10)
            mock_calculate_and_set_state.assert_called_with(10, 81, 100)
        api.send_device_command_properties.assert_called_with(
            "uuid", {"target_angle": 81}
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
            assert mock_async_update.called
        assert not entity.is_opening
        assert not entity.is_closing

    def test__set_state_CLOSING(self, entity):
        with patch.object(entity, "_start_moving_device") as mock_start_moving_device:
            entity._set_state(MovingState.CLOSING, delta=10, max_timedelta=100)
            mock_start_moving_device.assert_called_once_with(10)
        assert not entity.is_opening
        assert entity.is_closing

    def test__set_state_OPENING(self, entity):
        with patch.object(entity, "_start_moving_device") as mock_start_moving_device:
            entity._set_state(MovingState.OPENING, delta=10, max_timedelta=100)
            mock_start_moving_device.assert_called_once_with(10)
        assert entity.is_opening
        assert not entity.is_closing

    def test__end_moving_device(self, entity):
        with patch.object(entity, "stop_cover") as mock_stop_cover:
            entity._end_moving_device()
            assert mock_stop_cover.called

    def test__calculate_and_set_state_CLOSING(self, entity, device, api):
        device.drivetime_down = NumericValue(
            value=50, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.CLOSING
                entity._calculate_and_set_state(10, 100, -1)
                mock_calculate_state.assert_called_once_with(10, 100)
                mock_set_state.assert_called_once_with(
                    MovingState.CLOSING, delta=90, max_timedelta=50
                )
        assert api.device.called

    def test__calculate_and_set_state_OPENING(self, entity, device, api):
        device.drivetime_up = NumericValue(
            value=50, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.OPENING
                entity._calculate_and_set_state(100, 10, -1)
                mock_calculate_state.assert_called_once_with(100, 10)
                mock_set_state.assert_called_once_with(
                    MovingState.OPENING, delta=90, max_timedelta=50
                )
        assert api.device.called

    def test__calculate_and_set_state_tilt(self, entity):
        with patch.object(entity, "_set_state") as mock_set_state:
            with patch.object(entity, "_calculate_state") as mock_calculate_state:
                mock_calculate_state.return_value = MovingState.CLOSING
                entity._calculate_and_set_state(10, 100, 10)
                mock_calculate_state.assert_called_once_with(10, 100)
                mock_set_state.assert_called_once_with(
                    MovingState.CLOSING, delta=90, max_timedelta=10
                )

    def test__max_angle(self, entity):
        assert entity._max_angle == 90

    def test__max_angle_180(self, entity):
        entity._type = DeviceType.RAFFSTORE_180
        assert entity._max_angle == 180

    def test__max_angle_rollershutter(self, rollershutter_entity):
        assert rollershutter_entity._max_angle == 100

    def test__calculate_state_CLOSING(self, entity, device, api):
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        assert entity._calculate_state(100, 10) == MovingState.CLOSING
        assert api.device.called

    def test__calculate_state_OPENING(self, entity, device, api):
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        assert entity._calculate_state(10, 100) == MovingState.OPENING
        assert api.device.called

    def test__calculate_state_CLOSING_switched_drive_direction(
        self, entity, device, api
    ):
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        assert entity._calculate_state(10, 100) == MovingState.CLOSING
        assert api.device.called

    def test__calculate_state_OPENING_switched_drive_direction(
        self, entity, device, api
    ):
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        assert entity._calculate_state(100, 10) == MovingState.OPENING
        assert api.device.called

    def test__calculate_state_STILL(self, entity, api):
        api.device.return_value = None
        assert entity._calculate_state(10, 10) == MovingState.STILL
        assert not api.device.called

    def test__invert_position(self, entity, device, api):
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        assert entity._invert_position(10, 100) == 90
        assert api.device.called

    def test__invert_position_switched_drive_direction(self, entity, device, api):
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        assert entity._invert_position(10, 100) == 10
        assert api.device.called
