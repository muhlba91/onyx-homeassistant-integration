"""Test for the ONYX Light Entity."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.light import (
    ColorMode,
)
from homeassistant.core import HomeAssistant
from onyx_client.data.numeric_value import NumericValue
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
        assert len(entity.supported_features) == 0

    def test_color_mode(self, api, entity, device):
        device.device_type = DeviceType.BASIC_LIGHT
        api.device.return_value = device
        assert entity.color_mode == ColorMode.ONOFF
        assert len(entity.supported_color_modes) == 1
        assert entity.supported_color_modes[0] == ColorMode.ONOFF
        assert api.device.called

    def test_color_mode_brightness(self, api, dimmable_entity, device):
        device.device_type = DeviceType.DIMMABLE_LIGHT
        api.device.return_value = device
        assert dimmable_entity.color_mode == ColorMode.BRIGHTNESS
        assert len(dimmable_entity.supported_color_modes) == 1
        assert dimmable_entity.supported_color_modes[0] == ColorMode.BRIGHTNESS
        assert api.device.called

    def test_brightness(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=10, minimum=0, maximum=100, read_only=False
        )
        api.device.return_value = device
        assert entity.brightness == 25.5
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

    def test__get_dim_duration(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(90) == 50
        assert api.device.called

    def test__get_dim_duration_same(self, api, entity, device):
        device.actual_brightness = NumericValue(
            value=100, maximum=100, minimum=0, read_only=False
        )
        api.device.return_value = device
        assert entity._get_dim_duration(100) == 500
        assert api.device.called
