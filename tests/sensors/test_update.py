"""Test for the ONYX.CENTER Update Entity."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.exceptions import HomeAssistantError
from onyx_client.data.update_status import UpdateStatus

from custom_components.hella_onyx.const import (
    DOMAIN,
    UPDATE_CONTEXT,
    UPDATE_INSTALL_TIMEOUT,
)
from custom_components.hella_onyx.sensors.update import OnyxUpdate

from .helpers import make_api

MODULE = "custom_components.hella_onyx.sensors.update"
CURRENT = "2.13.4-0-geb8e366"


class TestOnyxUpdate:
    @pytest.fixture
    def api(self):
        api = make_api()
        api.update_status = UpdateStatus(CURRENT, "2.14.0")
        api.install_update = AsyncMock(return_value=True)
        api.last_update_success = True
        api.stream_drops = 0
        yield api

    @pytest.fixture
    def entity(self, api):
        entity = OnyxUpdate(api)
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        entity.device_entry = None
        yield entity

    def test_properties(self, entity):
        assert entity.name == "ONYX.CENTER Update"
        assert entity.unique_id == "finger/Update"
        assert entity.title == "ONYX.CENTER"
        assert entity.device_class == UpdateDeviceClass.FIRMWARE
        assert entity.supported_features == (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
        )
        assert entity.coordinator_context == UPDATE_CONTEXT

    def test_device_info(self, api, entity):
        info = entity.device_info
        assert info["identifiers"] == {(DOMAIN, "finger")}
        assert info["name"] == "ONYX.CENTER"
        assert info["manufacturer"] == "Hella"
        assert info["model"] == "ONYX.CENTER"
        assert info["sw_version"] == CURRENT
        api.update_status = None
        assert entity.device_info["sw_version"] is None

    def test_update_available(self, entity):
        assert entity.installed_version == CURRENT
        assert entity.latest_version == "2.14.0"
        assert entity.state == STATE_ON
        assert not entity.in_progress
        assert entity.update_percentage is None

    def test_older_available_version_is_offered(self, api, entity):
        api.update_status = UpdateStatus(CURRENT, "2.13.0")
        assert entity.state == STATE_ON

    def test_up_to_date(self, api, entity):
        api.update_status = UpdateStatus(CURRENT)
        assert entity.latest_version == CURRENT
        assert entity.state == STATE_OFF
        assert not entity.version_is_newer("2.14.0", CURRENT)

    def test_unknown_status(self, api, entity):
        api.update_status = None
        assert not entity.available
        assert entity.installed_version is None
        assert entity.latest_version is None
        assert entity.state is None
        assert not entity.in_progress
        assert entity.update_percentage is None
        assert not entity.version_is_newer("2.14.0", CURRENT)

    def test_available(self, api, entity):
        assert entity.available
        api.last_update_success = False
        assert not entity.available

    def test_transfer_progress(self, api, entity):
        api.update_status = UpdateStatus(CURRENT, "2.14.0", 0.4567)
        assert entity.in_progress
        assert entity.update_percentage == 45.7

    async def test_install(self, api, entity):
        with patch(f"{MODULE}.async_call_later") as call_later:
            await entity.async_install(None, False)
        api.install_update.assert_called_once_with()
        hass, delay, timeout = call_later.call_args.args
        assert hass is entity.hass
        assert delay == UPDATE_INSTALL_TIMEOUT
        assert timeout == entity._handle_install_timeout
        assert entity.in_progress
        assert entity.update_percentage is None
        # stays available while the ONYX.CENTER restarts
        api.last_update_success = False
        assert entity.available

    async def test_install_fails(self, api, entity):
        api.install_update.return_value = False
        with (
            patch(f"{MODULE}.async_call_later") as call_later,
            pytest.raises(HomeAssistantError),
        ):
            await entity.async_install(None, False)
        assert not call_later.called
        assert not entity.in_progress

    async def test_install_ends_with_new_version(self, api, entity):
        with patch(f"{MODULE}.async_call_later") as call_later:
            await entity.async_install(None, False)
        api.update_status = UpdateStatus(CURRENT, "2.14.0", 0.5)
        entity._handle_coordinator_update()
        assert entity.in_progress
        api.update_status = None
        entity._handle_coordinator_update()
        assert entity._installing is not None
        api.update_status = UpdateStatus("2.14.0-0-g0000000")
        entity._handle_coordinator_update()
        assert not entity.in_progress
        call_later.return_value.assert_called_once_with()
        assert entity._install_unsub is None
        assert entity.async_write_ha_state.called

    async def test_install_waits_for_restart(self, api, entity):
        with patch(f"{MODULE}.async_call_later"):
            await entity.async_install(None, False)
        # the transfer finished, the ONYX.CENTER did not restart yet
        api.update_status = UpdateStatus(CURRENT)
        entity._handle_coordinator_update()
        assert entity.in_progress
        # the stream dropped, the ONYX.CENTER is not back yet
        api.stream_drops = 1
        api.last_update_success = False
        entity._handle_coordinator_update()
        assert entity.in_progress
        api.last_update_success = True
        entity._handle_coordinator_update()
        assert not entity.in_progress

    async def test_install_ends_after_failed_restart(self, api, entity):
        api.stream_drops = 3
        with patch(f"{MODULE}.async_call_later"):
            await entity.async_install(None, False)
        entity._handle_coordinator_update()
        assert entity.in_progress
        # back with the same version and the update still offered
        api.stream_drops = 4
        entity._handle_coordinator_update()
        assert not entity.in_progress
        assert entity.state == STATE_ON

    def test_device_version_updated(self, api, entity):
        entity.device_entry = MagicMock(id="device", sw_version="2.13.0")
        with patch(f"{MODULE}.dr.async_get") as registry:
            entity._handle_coordinator_update()
            registry.return_value.async_update_device.assert_called_once_with(
                "device", sw_version=CURRENT
            )
            registry.reset_mock()
            entity.device_entry.sw_version = CURRENT
            entity._handle_coordinator_update()
            api.update_status = None
            entity._handle_coordinator_update()
        assert not registry.return_value.async_update_device.called

    async def test_install_timeout(self, api, entity):
        with patch(f"{MODULE}.async_call_later"):
            await entity.async_install(None, False)
        entity._handle_install_timeout(None)
        assert not entity.in_progress
        assert entity._install_unsub is None
        entity.async_write_ha_state.assert_called_once_with()

    async def test_repeated_install_replaces_timeout(self, entity):
        with patch(f"{MODULE}.async_call_later") as call_later:
            await entity.async_install(None, False)
            first = call_later.return_value
            call_later.return_value = MagicMock()
            await entity.async_install(None, False)
        first.assert_called_once_with()
        assert entity._install_unsub is call_later.return_value

    async def test_remove_cancels_timeout(self, entity):
        with patch(f"{MODULE}.async_call_later") as call_later:
            await entity.async_install(None, False)
        with patch(
            "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_will_remove_from_hass"
        ):
            await entity.async_will_remove_from_hass()
        call_later.return_value.assert_called_once_with()
        assert entity._install_unsub is None
