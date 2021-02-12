"""Test for the ONYX Entity."""

from unittest.mock import MagicMock

import pytest
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.onyx_entity import OnyxEntity


class TestOnyxEntity:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def coordinator(self):
        yield MagicMock()

    @pytest.fixture
    def entity(self, api, coordinator):
        yield OnyxEntity(api, coordinator, "name", DeviceType.RAFFSTORE_90, "uuid")

    def test_icon(self, entity):
        assert entity.icon == "mdi:window-shutter"

    def test_device_info(self, entity):
        assert entity.device_info == {
            "identifiers": {(DOMAIN, "uuid")},
            "name": "name",
            "manufacturer": "Hella",
            "model": "raffstore_90",
        }

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
