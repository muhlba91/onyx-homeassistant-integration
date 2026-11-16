"""Test for the ONYX Entity."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.helpers.device_registry import DeviceInfo
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.const import DOMAIN
from custom_components.hella_onyx.sensors.onyx_entity import OnyxEntity

from .helpers import NOW, animated, make_api, value

MODULE = "custom_components.hella_onyx.sensors.onyx_entity"


class TestOnyxEntity:
    @pytest.fixture
    def api(self):
        yield make_api()

    @pytest.fixture
    def entity(self, api):
        entity = OnyxEntity(api, "UTC", "name", DeviceType.RAFFSTORE_90, "uuid")
        entity.hass = MagicMock()
        entity.async_write_ha_state = MagicMock()
        yield entity

    @pytest.fixture
    def call_later(self):
        with patch(f"{MODULE}.async_call_later") as call_later:
            yield call_later

    @pytest.fixture
    def track_interval(self):
        with patch(f"{MODULE}.async_track_time_interval") as track_interval:
            yield track_interval

    def test_init(self, api, entity):
        assert entity.api == api
        assert entity.timezone == "UTC"
        assert entity.coordinator_context == "uuid"
        assert entity.icon == "mdi:help"
        assert entity.unique_id == "uuid/Device"
        assert entity.device_info == DeviceInfo(
            identifiers={(DOMAIN, "uuid")},
            name="name",
            manufacturer="Hella",
            model="raffstore_90",
        )

    def test_available(self, api, entity):
        api.last_update_success = True
        api.device.return_value = MagicMock()
        assert entity.available
        api.device.assert_called_with("uuid")
        api.device.return_value = None
        assert not entity.available

    def test_handle_coordinator_update(self, entity):
        with patch.object(entity, "_schedule_animation_updates") as schedule:
            entity._handle_coordinator_update()
            schedule.assert_called_once_with([])
        assert entity.async_write_ha_state.called

    async def test_added_schedules_animation_updates(self, entity):
        with (
            patch(
                "homeassistant.helpers.update_coordinator.CoordinatorEntity.async_added_to_hass"
            ) as added,
            patch.object(entity, "_schedule_animation_updates") as schedule,
        ):
            await entity.async_added_to_hass()
            assert added.called
            schedule.assert_called_once_with([])

    def test_numeric_value(self, api, entity):
        device = MagicMock()
        device.temperature = value(215)
        device.humidity = None
        device.wind_peak = value(None)
        api.device.return_value = device
        assert entity._numeric_value("temperature") == 215
        assert entity._numeric_value("temperature", 2) == 107.5
        assert entity._numeric_value("temperature", 10) == 21.5
        assert entity._numeric_value("humidity") is None
        assert entity._numeric_value("wind_peak") is None
        api.device.return_value = None
        assert entity._numeric_value("temperature") is None

    def test_end_time(self, entity):
        assert entity._end_time([None, value(10)]) is None
        assert entity._end_time([animated(0, 100, NOW - 1, 10)]) == NOW + 10
        assert (
            entity._end_time(
                [animated(0, 100, NOW - 1, 10), animated(0, 100, NOW, 20, delay=1)]
            )
            == NOW + 22
        )

    def test_end_time_within_additional_delay(self, entity):
        # ended 0.5 s ago, still within the additional delay of 1 s
        assert entity._end_time([animated(0, 100, NOW - 10.5, 10)]) == NOW + 0.5
        assert entity._end_time([animated(0, 100, NOW - 11.5, 10)]) is None

    def test_schedule_animation_updates(self, entity, call_later, track_interval):
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        assert track_interval.call_args.args[0] is entity.hass
        assert call_later.call_args.args[0] is entity.hass
        assert track_interval.call_args.args[1] == entity._handle_animation_update
        assert track_interval.call_args.args[2].total_seconds() == 5
        assert call_later.call_args.args[1] == pytest.approx(11.1)
        assert call_later.call_args.args[2] == entity._handle_animation_end
        assert len(entity._animation_unsubs) == 2

    def test_schedule_animation_updates_every_second(
        self, api, entity, call_later, track_interval
    ):
        api.config.interpolation_frequency = 1
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        assert track_interval.call_args.args[2].total_seconds() == 1

    def test_schedule_animation_updates_without_interpolation(
        self, api, entity, call_later, track_interval
    ):
        api.config.interpolation_frequency = 0
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        assert not track_interval.called
        assert call_later.called

    def test_schedule_animation_updates_cancels_previous(
        self, entity, call_later, track_interval
    ):
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        unsubs = list(entity._animation_unsubs)
        entity._schedule_animation_updates([value(100)])
        for unsub in unsubs:
            unsub.assert_called_once_with()
        assert entity._animation_unsubs == []

    def test_handle_animation_update(self, entity):
        entity._handle_animation_update()
        assert entity.async_write_ha_state.called

    def test_handle_animation_end(self, entity, call_later, track_interval):
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        entity._handle_animation_end()
        assert entity._animation_unsubs == []
        assert entity.async_write_ha_state.called

    async def test_will_remove_cancels_timers(self, entity, call_later, track_interval):
        entity._schedule_animation_updates([animated(0, 100, NOW, 10)])
        unsubs = list(entity._animation_unsubs)
        await entity.async_will_remove_from_hass()
        for unsub in unsubs:
            unsub.assert_called_once_with()
