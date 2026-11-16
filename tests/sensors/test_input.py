"""Test for the ONYX Input Binary Sensor."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.enum_value import EnumValue
from onyx_client.device.input import Input
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.input import OnyxBinarySensorInput


class TestOnyxBinarySensorInput:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def device(self, api):
        device = Input(
            "uuid",
            "name",
            DeviceType.INPUT,
            DeviceMode(DeviceType.INPUT),
            [],
            input_type=EnumValue("rain_sensor", [], True),
            input_active=EnumValue("true", ["true", "false"], True),
        )
        api.device.return_value = device
        yield device

    @pytest.fixture
    def entity(self, api):
        yield OnyxBinarySensorInput(api, "UTC", "name", DeviceType.INPUT, "uuid")

    def test_properties(self, entity):
        assert entity.name == "name"
        assert entity.unique_id == "uuid/Input"
        assert entity.icon is None

    @pytest.mark.parametrize(
        ("input_type", "device_class"),
        [
            ("rain_sensor", BinarySensorDeviceClass.MOISTURE),
            ("fire_alarm", BinarySensorDeviceClass.SMOKE),
            ("wind_alarm", BinarySensorDeviceClass.SAFETY),
            ("generic_alarm", BinarySensorDeviceClass.SAFETY),
            ("future_alarm", None),
            (None, None),
        ],
    )
    def test_device_class(self, entity, device, input_type, device_class):
        device.input_type = EnumValue(input_type, [], True)
        assert entity.device_class == device_class

    def test_device_class_unknown(self, api, entity, device):
        device.input_type = None
        assert entity.device_class is None
        api.device.return_value = None
        assert entity.device_class is None

    def test_is_on(self, entity, device):
        assert entity.is_on is True
        device.input_active = EnumValue("false", [], True)
        assert entity.is_on is False
        device.input_active = EnumValue(None, [], True)
        assert entity.is_on is None

    def test_is_on_unknown(self, api, entity, device):
        device.input_active = None
        assert entity.is_on is None
        api.device.return_value = None
        assert entity.is_on is None
