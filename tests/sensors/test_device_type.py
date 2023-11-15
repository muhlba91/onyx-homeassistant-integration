"""Test for the ONYX Device Type Sensor."""

from unittest.mock import MagicMock

import pytest
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.device_type import OnyxSensorDeviceType


class TestOnyxSensorDeviceType:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def coordinator(self):
        yield MagicMock()

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
    def entity(self, api, coordinator):
        yield OnyxSensorDeviceType(
            api, "UTC", coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:cellphone-link"

    def test_name(self, entity):
        assert entity.name == "name Device Type"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/DeviceType"

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == DeviceType.RAFFSTORE_90.string()
        assert api.device.called
