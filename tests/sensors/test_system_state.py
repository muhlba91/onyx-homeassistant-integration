"""Test for the ONYX System State Sensor."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.enum_value import EnumValue
from onyx_client.device.shutter import Shutter
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.system_state import OnyxSensorSystemState

VALUES = ["collision", "collision_not_calibrated", "not_calibrated", "ok"]


class TestOnyxSensorSystemState:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def device(self, api):
        device = Shutter(
            "uuid",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            [],
            system_state=EnumValue("ok", list(VALUES), True),
        )
        api.device.return_value = device
        yield device

    @pytest.fixture
    def entity(self, api):
        yield OnyxSensorSystemState(api, "UTC", "name", DeviceType.RAFFSTORE_90, "uuid")

    def test_properties(self, entity):
        assert entity.name == "name System State"
        assert entity.unique_id == "uuid/SystemState"
        assert entity.icon == "mdi:alert-circle-check-outline"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC
        assert entity.device_class == SensorDeviceClass.ENUM

    def test_state(self, entity, device):
        assert entity.native_value == "ok"
        assert entity.options == VALUES
        device.system_state = EnumValue("collision", list(VALUES), True)
        assert entity.native_value == "collision"

    def test_undocumented_state(self, entity, device):
        device.system_state = EnumValue("overheated", list(VALUES), True)
        assert entity.native_value == "overheated"
        assert entity.options == [*VALUES, "overheated"]
        assert device.system_state.values == VALUES

    def test_state_without_value(self, entity, device):
        device.system_state = EnumValue(None, list(VALUES), True)
        assert entity.native_value is None
        assert entity.options == VALUES

    def test_state_unknown(self, api, entity, device):
        device.system_state = None
        assert entity.native_value is None
        assert entity.options is None
        api.device.return_value = None
        assert entity.native_value is None
        assert entity.options is None
