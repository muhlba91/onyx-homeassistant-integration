"""Test for the LED-Pi Sensor Entities."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TIME_MILLISECONDS
from onyx_client.data.boolean_value import BooleanValue
from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN, ONYX_API, ONYX_COORDINATOR
from custom_components.hella_onyx.sensor import (
    OnyxSensorDeviceType,
    OnyxSensorDriveTimeDown,
    OnyxSensorDriveTimeUp,
    OnyxSensorRotationTime,
    OnyxSensorSwitchDriveDirection,
    async_setup_entry,
)


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass):
    config_entry = ConfigEntry(1, DOMAIN, "entry", {}, "source", "POLL", {})

    class AsyncAddEntries:
        def __init__(self):
            self.called_async_add_entities = False

        def call(self, sensors, boolean):
            self.called_async_add_entities = True

    async_add_entries = AsyncAddEntries()

    mock_hass.data.return_value = {
        DOMAIN: {"entry_id": {ONYX_API: None, ONYX_COORDINATOR: None}}
    }

    await async_setup_entry(mock_hass, config_entry, async_add_entries.call)
    assert async_add_entries.called_async_add_entities


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
            api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
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


class TestOnyxSensorSwitchDriveDirection:
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
        yield OnyxSensorSwitchDriveDirection(
            api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:directions-fork"

    def test_name(self, entity):
        assert entity.name == "name Switch Drive Direction"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/SwitchDriveDirection"

    def test_state_false(self, api, entity, device):
        device.switch_drive_direction = BooleanValue(value=False, read_only=True)
        api.device.return_value = device
        assert not entity.state
        assert api.device.called

    def test_state_true(self, api, entity, device):
        device.switch_drive_direction = BooleanValue(value=True, read_only=True)
        api.device.return_value = device
        assert entity.state
        assert api.device.called


class TestOnyxSensorDriveTimeUp:
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
        yield OnyxSensorDriveTimeUp(
            api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:arrow-up"

    def test_name(self, entity):
        assert entity.name == "name Drive Time Up"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/DriveTimeUp"

    def test_state(self, api, entity, device):
        device.drivetime_up = NumericValue(
            value=10, minimum=1, maximum=10, read_only=True
        )
        api.device.return_value = device
        assert entity.state == 10
        assert api.device.called

    def test_unit_of_measurement(self, api, entity, device):
        assert entity.unit_of_measurement == TIME_MILLISECONDS


class TestOnyxSensorDriveTimeDown:
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
        yield OnyxSensorDriveTimeDown(
            api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:arrow-down"

    def test_name(self, entity):
        assert entity.name == "name Drive Time Down"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/DriveTimeDown"

    def test_state(self, api, entity, device):
        device.drivetime_down = NumericValue(
            value=10, minimum=1, maximum=10, read_only=True
        )
        api.device.return_value = device
        assert entity.state == 10
        assert api.device.called

    def test_unit_of_measurement(self, api, entity, device):
        assert entity.unit_of_measurement == TIME_MILLISECONDS


class TestOnyxSensorRotationTime:
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
        yield OnyxSensorRotationTime(
            api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid"
        )

    def test_icon(self, entity):
        assert entity.icon == "mdi:rotate-3d-variant"

    def test_name(self, entity):
        assert entity.name == "name Rotation Time"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/RotationTime"

    def test_state(self, api, entity, device):
        device.rotationtime = NumericValue(
            value=10, minimum=1, maximum=10, read_only=True
        )
        api.device.return_value = device
        assert entity.state == 10
        assert api.device.called

    def test_unit_of_measurement(self, api, entity, device):
        assert entity.unit_of_measurement == TIME_MILLISECONDS
