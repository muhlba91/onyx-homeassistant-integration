"""Test for the ONYX Active Command Sensor."""

from unittest.mock import MagicMock

import pytest
from homeassistant.const import EntityCategory
from onyx_client.data.active_command import ActiveCommand
from onyx_client.data.command_source import CommandSource
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.command_attribute import CommandAttribute
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.active_command import (
    NO_COMMAND,
    UNATTRIBUTED,
    OnyxSensorActiveCommand,
)


def command(source=None, action=None):
    """An active command with the given source and action."""
    return ActiveCommand(
        source,
        action,
        {"target_position": 0},
        [CommandAttribute.FAST, None],
        1527510327,
        1527510900,
        ["wind"],
    )


class TestOnyxSensorActiveCommand:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def device(self, api):
        device = Shutter(
            "uuid",
            "name",
            DeviceType.ROLLERSHUTTER,
            DeviceMode(DeviceType.ROLLERSHUTTER),
            [],
        )
        api.device.return_value = device
        yield device

    @pytest.fixture
    def entity(self, api):
        yield OnyxSensorActiveCommand(
            api, "UTC", "name", DeviceType.ROLLERSHUTTER, "uuid"
        )

    def test_properties(self, entity):
        assert entity.name == "name Active Command"
        assert entity.unique_id == "uuid/ActiveCommand"
        assert entity.icon == "mdi:console"
        assert entity.entity_category == EntityCategory.DIAGNOSTIC

    def test_unrecorded_attributes(self, entity, device):
        device.active_command = command(
            CommandSource("automation", "id", "Wind protection", "🌬")
        )
        assert set(entity.extra_state_attributes) == entity._unrecorded_attributes

    def test_no_command(self, entity, device):
        assert entity.native_value == NO_COMMAND
        assert entity.extra_state_attributes is None

    def test_unknown_device(self, api, entity):
        api.device.return_value = None
        assert entity.native_value is None
        assert entity.extra_state_attributes is None

    def test_command(self, entity, device):
        device.active_command = command(
            CommandSource("automation", "id", "Wind protection", "🌬"), Action.CLOSE
        )
        assert entity.native_value == "automation"
        assert entity.extra_state_attributes == {
            "source_name": "Wind protection",
            "source_id": "id",
            "action": "close",
            "properties": {"target_position": 0},
            "attributes": ["fast"],
            "active_indicators": ["wind"],
            "valid_from": "2018-05-28T12:25:27+00:00",
            "best_before": "2018-05-28T12:35:00+00:00",
        }

    def test_unattributed_command(self, entity, device):
        device.active_command = command()
        assert entity.native_value == UNATTRIBUTED
        attributes = entity.extra_state_attributes
        assert attributes["source_name"] is None
        assert attributes["source_id"] is None
        assert attributes["action"] is None
        device.active_command = command(CommandSource(None, None, None, None))
        assert entity.native_value == UNATTRIBUTED

    @pytest.mark.parametrize("timestamp", [10**20, "invalid"])
    def test_command_with_invalid_validity(self, entity, device, timestamp):
        device.active_command = ActiveCommand(
            None, None, None, [], timestamp, timestamp, []
        )
        attributes = entity.extra_state_attributes
        assert attributes["valid_from"] is None
        assert attributes["best_before"] is None

    def test_command_without_validity(self, entity, device):
        device.active_command = ActiveCommand(None, None, None, [], None, None, [])
        attributes = entity.extra_state_attributes
        assert attributes["valid_from"] is None
        assert attributes["best_before"] is None
