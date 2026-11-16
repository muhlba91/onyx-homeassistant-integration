"""Test for the ONYX Automation Switch."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from onyx_client.data.automation import Automation

from custom_components.hella_onyx.const import AUTOMATION_CONTEXT, DOMAIN
from custom_components.hella_onyx.sensors.automation import OnyxAutomationSwitch

from .helpers import make_api

WIND = "http://o.hella.info/d/sensor/scenarios?type=info.hella.onyx.wind"


class TestOnyxAutomationSwitch:
    @pytest.fixture
    def api(self):
        api = make_api()
        automations = {
            "uuid": Automation("uuid", "Evening shade", "🌆", "sun", True),
            WIND: Automation(WIND, None, None, "info.hella.onyx.wind", False),
        }
        api.automation.side_effect = automations.get
        api.devices = {"sensor": MagicMock()}
        api.devices["sensor"].name = "Weather"
        api.set_automation_enabled = AsyncMock(return_value=True)
        api.last_update_success = True
        yield api

    def create(self, api, identifier="uuid"):
        entity = OnyxAutomationSwitch(api, identifier)
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        return entity

    @pytest.fixture
    def entity(self, api):
        yield self.create(api)

    def test_properties(self, entity):
        assert entity.name == "Evening shade Automation"
        assert entity.unique_id == "finger/Automation/uuid"
        assert entity.icon == "mdi:robot"
        assert entity.entity_category == EntityCategory.CONFIG
        assert not entity.entity_registry_enabled_default
        assert entity.coordinator_context == AUTOMATION_CONTEXT

    def test_device_info(self, entity):
        info = entity.device_info
        assert info["identifiers"] == {(DOMAIN, "finger")}
        assert info["name"] == "ONYX.CENTER"
        assert info["sw_version"] is None

    def test_state(self, api, entity):
        assert entity.available
        assert entity.is_on
        assert entity.extra_state_attributes == {
            "automation_id": "uuid",
            "automation_type": "sun",
            "emoji": "🌆",
        }
        assert not self.create(api, WIND).is_on

    def test_removed(self, api):
        entity = self.create(api, "removed")
        assert not entity.available
        assert entity.is_on is None
        assert entity.extra_state_attributes is None
        assert entity.name == "removed Automation"

    def test_unavailable_coordinator(self, api, entity):
        api.last_update_success = False
        assert not entity.available

    def test_name_of_device(self, api):
        assert self.create(api, WIND).name == "Weather Automation"

    def test_name_of_type(self, api):
        api.devices = {}
        assert self.create(api, WIND).name == "info.hella.onyx.wind Automation"

    async def test_turn_on(self, api, entity):
        await entity.async_turn_on()
        api.set_automation_enabled.assert_called_once_with("uuid", True)

    async def test_turn_off(self, api, entity):
        await entity.async_turn_off()
        api.set_automation_enabled.assert_called_once_with("uuid", False)

    async def test_switch_failed(self, api, entity):
        api.set_automation_enabled.return_value = False
        with pytest.raises(HomeAssistantError, match="did not disable"):
            await entity.async_turn_off()
        with pytest.raises(HomeAssistantError, match="did not enable"):
            await entity.async_turn_on()
