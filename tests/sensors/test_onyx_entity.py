"""Test for the ONYX Entity."""

import pytest

from unittest.mock import MagicMock

from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.api_connector import UnknownStateException
from custom_components.hella_onyx.sensors.onyx_entity import OnyxEntity


class TestOnyxEntity:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def entity(self, api):
        entity = OnyxEntity(api, "UTC", "name", DeviceType.RAFFSTORE_90, "uuid")
        entity.async_write_ha_state = MagicMock()
        yield entity

    def test_init_properties(self, entity, api):
        assert entity.coordinator == api
        assert entity.api == api
        assert entity.timezone == "UTC"
        assert entity._name == "name"
        assert entity._type == DeviceType.RAFFSTORE_90
        assert entity._uuid == "uuid"

    def test_icon(self, entity):
        assert entity.icon == "mdi:help"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Device"

    def test_device_info(self, entity):
        device_info = entity.device_info
        assert (DOMAIN, "uuid") in device_info["identifiers"]
        assert device_info["name"] == "name"
        assert device_info["manufacturer"] == "Hella"
        assert device_info["model"] == "raffstore_90"

    def test__device(self, entity, api):
        device = Shutter(
            "id",
            "name",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )
        api.device.return_value = device
        assert entity._device == device

    def test__device_unknown_state_returns_none(self, entity, api):
        """When the UUID is no longer in the coordinator, _device returns None."""
        api.device.side_effect = UnknownStateException("UNKNOWN_DEVICE")
        assert entity._device is None
