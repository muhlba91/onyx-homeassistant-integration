"""Test for the ONYX Identify Button."""

import pytest
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.const import EntityCategory
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.identify import OnyxButtonIdentify

from .helpers import make_api


class TestOnyxButtonIdentify:
    @pytest.fixture
    def api(self):
        yield make_api()

    @pytest.fixture
    def entity(self, api):
        yield OnyxButtonIdentify(api, "UTC", "name", DeviceType.INPUT, "uuid")

    def test_properties(self, entity):
        assert entity.name == "name Identify"
        assert entity.unique_id == "uuid/Identify"
        assert entity.icon is None
        assert entity.device_class == ButtonDeviceClass.IDENTIFY
        assert entity.entity_category == EntityCategory.CONFIG
        assert entity.entity_registry_enabled_default is False

    async def test_press(self, api, entity):
        await entity.async_press()
        api.send_device_command_action.assert_called_once_with("uuid", Action.WINK)
