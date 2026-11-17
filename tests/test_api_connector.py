"""Test for the ONYX API Connector."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientConnectionError, ClientResponseError, InvalidURL
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    HomeAssistantError,
)
from homeassistant.helpers.update_coordinator import UpdateFailed
from onyx_client.client import OnyxClient
from onyx_client.data.update_status import UpdateStatus
from onyx_client.enum.action import Action
from onyx_client.enum.verify_result import VerifyResult
from onyx_client.group.group import Group
from onyx_client.stream.events import (
    AutomationsChanged,
    DeviceAdded,
    DeviceChanged,
    DeviceRemoved,
    GroupsChanged,
    Pulse,
    Resynced,
    UpdateChanged,
)

from custom_components.hella_onyx.api_connector import APIConnector, CommandException
from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.const import (
    AUTOMATION_CONTEXT,
    COMMAND_RETRY_DELAY_MAX,
    COMMAND_RETRY_DELAY_MIN,
    COMMAND_TIMEOUT,
    DEFAULT_ADDITIONAL_DELAY,
    DEFAULT_CLOSED_TOLERANCE,
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MOVING_TIMEOUT,
    STREAM_CHECK_INTERVAL,
    STREAM_RESTART_DELAY,
    STREAM_SILENCE_TIMEOUT,
    UPDATE_CONTEXT,
)

from .helpers import MODULE, FakeClient, automation, shutter, snapshot


class TestAPIConnector:
    @pytest.fixture
    def config(self):
        yield Configuration(
            60,
            DEFAULT_MIN_DIM_DURATION,
            DEFAULT_MAX_DIM_DURATION,
            DEFAULT_ADDITIONAL_DELAY,
            DEFAULT_INTERPOLATION_FREQUENCY,
            DEFAULT_CLOSED_TOLERANCE,
            DEFAULT_MOVING_TIMEOUT,
            "finger",
            "token",
            None,
        )

    @pytest.fixture
    def entry(self):
        entry = MagicMock()
        entry.entry_id = "entry"
        yield entry

    @pytest.fixture
    def client(self):
        yield FakeClient([snapshot(shutter("a"))])

    @pytest.fixture
    async def api(self, hass, config, entry, client):
        api = APIConnector(hass, config)
        api.config_entry = entry
        api._APIConnector__client = client
        yield api
        await api._stop_stream()

    async def test_init(self, hass, config):
        api = APIConnector(hass, config)
        assert api.name == "hella_onyx"
        assert api.config == config
        assert api.update_interval.total_seconds() == 3600
        assert api.devices == {}
        assert api.groups == {}
        assert api.data["automations"] == []
        assert api.data["update"] is None

    async def test_client(self, hass, config):
        api = APIConnector(hass, config)
        client = api._client()
        assert isinstance(client, OnyxClient)
        assert client.config.fingerprint == "finger"
        assert client.config.access_token == "token"
        assert api._client() is client

    async def test_client_arguments(self, hass, config):
        config.local_address = "10.0.0.1"
        api = APIConnector(hass, config)
        with (
            patch("custom_components.hella_onyx.api_connector.create") as create,
            patch(
                "custom_components.hella_onyx.api_connector.async_get_clientsession"
            ) as session,
        ):
            api._client()
        session.assert_called_once_with(hass)
        create.assert_called_once_with(
            fingerprint="finger",
            access_token="token",
            client_session=session.return_value,
            local_address="10.0.0.1",
        )

    async def test_first_update_waits_for_snapshot(self, api, client):
        data = await api._async_update_data()
        assert client.verify.called
        assert list(data["devices"]) == ["a"]
        assert list(data["groups"]) == ["group"]
        assert data["update"].current == "2.13.4"
        assert data["automations"] == []
        assert api.device("a").identifier == "a"
        assert api.device("unknown") is None
        assert not client.resync.called

    async def test_update_resyncs_running_stream(self, api, client):
        await api._async_update_data()
        data = await api._async_update_data()
        assert client.resync.called
        assert data is api.data
        assert client.verify.call_count == 1

    async def test_update_restarts_ended_stream(self, api, client):
        client.error = ClientResponseError(MagicMock(), (), status=500)
        await api._async_update_data()
        await asyncio.sleep(0)
        assert api._stream_task.done()
        client.error = None
        await api._async_update_data()
        assert client.verify.call_count == 2
        assert not client.resync.called

    @pytest.mark.parametrize(
        ("result", "exception"),
        [
            (VerifyResult.UNAUTHORIZED, ConfigEntryAuthFailed),
            (VerifyResult.VERSION_UNSUPPORTED, ConfigEntryError),
            (VerifyResult.UNREACHABLE, UpdateFailed),
        ],
    )
    async def test_update_verify_fails(self, api, client, result, exception):
        client.verify.return_value = result
        with pytest.raises(exception):
            await api._async_update_data()
        assert api._stream_task is None

    async def test_update_without_snapshot(self, api, client):
        client.events = []
        with (
            patch("custom_components.hella_onyx.api_connector.SNAPSHOT_TIMEOUT", 0),
            pytest.raises(UpdateFailed),
        ):
            await api._async_update_data()
        assert client.close.called
        assert api._stream_task is None
        assert api._APIConnector__client is None

    async def test_stream_fails_unexpectedly(self, api, client):
        client.error = RuntimeError("boom")
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        with patch(f"{MODULE}.async_call_later") as call_later:
            await api._async_update_data()
            await api._stream_task
        assert api._stream_task.exception() is None
        assert not api.last_update_success
        assert listener.called
        hass, delay, restart = call_later.call_args.args
        assert hass is api.hass
        assert delay == STREAM_RESTART_DELAY
        assert restart == api._handle_stream_restart
        assert api._restart_unsub is call_later.return_value

    async def test_stream_restart(self, api, client):
        client.error = RuntimeError("boom")
        with patch(f"{MODULE}.async_call_later"):
            await api._async_update_data()
            await api._stream_task
        client.error = None
        with patch.object(api, "async_request_refresh") as refresh:
            api._handle_stream_restart(None)
            await asyncio.sleep(0)
        refresh.assert_called_once_with()
        assert api._restart_unsub is None
        await api.async_refresh()
        assert api.last_update_success
        assert not api._restarting
        assert client.verify.call_count == 2

    async def test_failed_restart_retries(self, api, client):
        api._restarting = True
        client.verify.return_value = VerifyResult.UNREACHABLE
        with (
            patch(f"{MODULE}.async_call_later") as call_later,
            pytest.raises(UpdateFailed),
        ):
            await api._async_update_data()
        assert call_later.call_args.args[1] == STREAM_RESTART_DELAY
        assert api._restarting

    async def test_failed_start_without_restart_does_not_retry(self, api, client):
        client.verify.return_value = VerifyResult.UNREACHABLE
        with (
            patch(f"{MODULE}.async_call_later") as call_later,
            pytest.raises(UpdateFailed),
        ):
            await api._async_update_data()
        assert not call_later.called

    async def test_no_restart_after_shutdown(self, api, client):
        api._restarting = True
        api._shutdown_requested = True
        with (
            patch(f"{MODULE}.async_call_later") as call_later,
            pytest.raises(UpdateFailed),
        ):
            await api._async_update_data()
        assert not call_later.called
        assert api._stream_task is None

    async def test_shutdown_cancels_restart(self, api):
        unsub = MagicMock()
        api._restart_unsub = unsub
        await api.async_shutdown()
        unsub.assert_called_once_with()

    async def test_concurrent_updates_start_one_stream(self, api, client):
        await asyncio.gather(api._async_update_data(), api._async_update_data())
        assert client.verify.call_count == 1
        assert client.resync.call_count == 1

    async def test_update_cancels_pending_restart(self, api):
        unsub = MagicMock()
        api._restart_unsub = unsub
        await api._async_update_data()
        unsub.assert_called_once_with()
        assert api._restart_unsub is None

    @pytest.mark.parametrize(
        "error",
        [RuntimeError("boom"), ClientResponseError(MagicMock(), (), status=401)],
    )
    async def test_failure_of_stopped_stream_is_ignored(
        self, hass, api, client, entry, error
    ):
        async def stream():
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                # e.g. closing the client fails while the stream is stopped
                raise error from None
            yield

        client.stream = stream
        with patch(f"{MODULE}.async_call_later") as call_later:
            task = hass.async_create_background_task(api._stream(), "stream")
            await asyncio.sleep(0)
            task.cancel()
            await task
        assert api.last_update_success
        assert not call_later.called
        assert not entry.async_start_reauth.called

    async def test_stop_stream_cancels_restart(self, api):
        unsub = MagicMock()
        api._restart_unsub = unsub
        await api._stop_stream()
        unsub.assert_called_once_with()
        assert api._restart_unsub is None

    async def test_stop_stream_detaches_task_before_closing(self, api, client):
        await api._async_update_data()
        task = api._stream_task

        async def close():
            assert api._stream_task is None
            assert task.cancelling()

        client.close.side_effect = close
        await api._stop_stream()
        assert client.close.called

    async def test_stream_rejected_starts_reauth(self, api, client, entry):
        client.error = ClientResponseError(MagicMock(), (), status=401)
        await api._async_update_data()
        await api._stream_task
        entry.async_start_reauth.assert_called_once_with(api.hass)
        assert not api.last_update_success
        assert api._restart_unsub is None

    async def test_shutdown(self, api, client):
        await api._async_update_data()
        task = api._stream_task
        await api.async_shutdown()
        await asyncio.sleep(0)
        assert client.close.called
        assert task.cancelled()
        assert api._stream_task is None

    async def test_shutdown_without_client(self, hass, config):
        api = APIConnector(hass, config)
        await api.async_shutdown()
        assert api._stream_task is None

    async def test_stream_check_started_once_and_stopped(self, api, client):
        client.error = RuntimeError("boom")
        with (
            patch(f"{MODULE}.async_track_time_interval") as track,
            patch(f"{MODULE}.async_call_later"),
        ):
            await api._async_update_data()
            await api._stream_task
            client.error = None
            await api._async_update_data()
        hass, check, interval = track.call_args.args
        assert hass is api.hass
        assert check == api._check_stream
        assert interval.total_seconds() == STREAM_CHECK_INTERVAL
        assert track.call_count == 1
        await api._stop_stream()
        track.return_value.assert_called_once_with()
        assert api._check_unsub is None

    async def test_silent_stream_marks_unavailable(self, api):
        await api._async_update_data()
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        now = 1000.0  # exactly representable, so the boundary is not off by rounding
        with patch(f"{MODULE}.time.monotonic", return_value=now + 1):
            api._handle_event(Pulse(1.0))
        with patch(
            f"{MODULE}.time.monotonic",
            return_value=now + 1 + STREAM_SILENCE_TIMEOUT,
        ):
            api._check_stream(None)
            assert api.last_update_success
        with patch(
            f"{MODULE}.time.monotonic",
            return_value=now + 2 + STREAM_SILENCE_TIMEOUT,
        ):
            api._check_stream(None)
            assert not api.last_update_success
            assert isinstance(api.last_exception, UpdateFailed)
            assert listener.call_count == 1
            api._check_stream(None)
            assert listener.call_count == 1

    @pytest.mark.parametrize("event", [snapshot(shutter("a")), Pulse(1.0)])
    async def test_event_after_silence_marks_available(self, api, event):
        await api._async_update_data()
        api._last_event -= STREAM_SILENCE_TIMEOUT + 1
        api._check_stream(None)
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(Resynced("timeout"))
        assert not api.last_update_success
        assert not listener.called
        api._handle_event(event)
        assert api.last_update_success
        listener.assert_called_once_with()
        assert not api._silent

    async def test_event_without_stream_keeps_failure(self, api, client):
        api._handle_event(Pulse(1.0))
        api.last_update_success = False
        api._handle_event(snapshot(shutter("a")))
        assert not api.last_update_success
        client.error = RuntimeError("boom")
        with patch(f"{MODULE}.async_call_later"):
            await api._async_update_data()
            await api._stream_task
        api._handle_event(Pulse(1.0))
        assert not api.last_update_success

    async def test_resync_during_silence_is_no_request(self, api, client):
        await api._async_update_data()
        api._last_event -= STREAM_SILENCE_TIMEOUT + 1
        with pytest.raises(UpdateFailed):
            await api._async_update_data()
        api._handle_event(Resynced("timeout"))
        assert api.stream_drops == 1

    async def test_stream_start_resets_flags(self, api, client):
        client.error = RuntimeError("boom")
        with patch(f"{MODULE}.async_call_later"):
            await api._async_update_data()
            await api._stream_task
        api._resync_requested = True
        api._silent = True
        client.error = None
        await api._async_update_data()
        assert not api._resync_requested
        assert not api._silent

    async def test_stream_drops(self, api, client):
        await api._async_update_data()
        api._handle_event(Resynced("timeout"))
        assert api.stream_drops == 1
        await api._async_update_data()
        api._handle_event(Resynced("resync requested"))
        assert api.stream_drops == 1
        api._handle_event(Resynced("timeout"))
        assert api.stream_drops == 2

    async def test_no_stream_check_after_shutdown(self, api, client):
        async def stream():
            api._shutdown_requested = True
            yield snapshot(shutter("a"))
            await asyncio.Event().wait()

        client.stream = stream
        with patch(f"{MODULE}.async_track_time_interval") as track:
            await api._async_update_data()
        assert not track.called
        assert api._check_unsub is None

    async def test_check_ignores_ended_stream(self, api, client):
        api._check_stream(None)
        assert api.last_update_success
        client.error = RuntimeError("boom")
        with patch(f"{MODULE}.async_call_later"):
            await api._async_update_data()
            await api._stream_task
        api.last_update_success = True
        api._last_event -= STREAM_SILENCE_TIMEOUT + 1
        api._check_stream(None)
        assert api.last_update_success

    async def test_resync_of_silent_stream_fails(self, api, client):
        await api._async_update_data()
        api._last_event -= STREAM_SILENCE_TIMEOUT + 1
        with pytest.raises(UpdateFailed):
            await api._async_update_data()
        assert client.resync.called

    async def test_device_changed_updates_only_its_listeners(self, api):
        api._handle_event(snapshot(shutter("a"), shutter("b")))
        listener_a = MagicMock()
        listener_b = MagicMock()
        api.async_add_listener(listener_a, "a")
        api.async_add_listener(listener_b, "b")

        device = shutter("a", 50)
        api._handle_event(DeviceChanged(device))
        assert api.device("a") is device
        assert listener_a.called
        assert not listener_b.called

    async def test_device_removed(self, api):
        api._handle_event(snapshot(shutter("a")))
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(DeviceRemoved("a"))
        api._handle_event(DeviceRemoved("unknown"))
        assert api.device("a") is None
        assert listener.call_count == 1

    async def test_snapshot_updates_all_listeners(self, api):
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(snapshot(shutter("a")))
        assert listener.called

    async def test_device_added_reloads(self, hass, api, entry):
        api._handle_event(snapshot(shutter("a")))
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            device = shutter("a")
            api._handle_event(DeviceAdded(device))
            assert not reload.called
            assert listener.called
            assert api.device("a") is device
            api._handle_event(DeviceAdded(shutter("b")))
            api._handle_event(DeviceAdded(shutter("b")))
            api._handle_event(snapshot(shutter("a"), shutter("b")))
            reload.assert_called_once_with("entry")
        assert api.device("b") is not None

    async def test_snapshot_with_new_device_reloads(self, hass, api):
        api._handle_event(snapshot(shutter("a"), shutter("b")))
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(snapshot(shutter("a")))
            assert not reload.called
            api._handle_event(snapshot(shutter("a"), shutter("c")))
            reload.assert_called_once_with("entry")

    async def test_reload_without_entry(self, hass, config):
        api = APIConnector(hass, config)
        api._handle_event(snapshot())
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(DeviceAdded(shutter("a")))
            assert not reload.called

    async def test_collections_changed(self, api):
        api._handle_event(snapshot(shutter("a"), automations=[automation("x")]))
        groups = {"other": Group("other", "Other", [])}
        api._handle_event(GroupsChanged(groups))
        automations = [automation("x")]
        api._handle_event(AutomationsChanged(automations))
        api._handle_event(UpdateChanged(UpdateStatus("2.14.0")))
        api._handle_event(Pulse(1.0))
        assert api.groups == groups
        assert api.automations is automations
        assert api.data["update"].current == "2.14.0"
        assert api.update_status is api.data["update"]

    async def test_automation(self, api):
        api._handle_event(snapshot(automations=[automation("x"), automation("y")]))
        assert api.automation("y").identifier == "y"
        assert api.automation("unknown") is None

    async def test_automations_changed_updates_only_its_listeners(self, hass, api):
        api._handle_event(snapshot(shutter("a"), automations=[automation("x")]))
        automation_listener = MagicMock()
        device_listener = MagicMock()
        api.async_add_listener(automation_listener, AUTOMATION_CONTEXT)
        api.async_add_listener(device_listener, "a")
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(AutomationsChanged([automation("x", False)]))
            api._handle_event(AutomationsChanged([]))
            assert not reload.called
        assert automation_listener.call_count == 2
        assert not device_listener.called

    async def test_new_automations_reload(self, hass, api):
        api._handle_event(snapshot(automations=[automation("x")]))
        with patch.object(hass.config_entries, "async_schedule_reload") as reload:
            api._handle_event(AutomationsChanged([automation("x"), automation("y")]))
            api._handle_event(snapshot(automations=[automation("y")]))
            reload.assert_called_once_with("entry")
            api._handle_event(snapshot(automations=[automation("z")]))
            assert reload.call_count == 2

    @pytest.mark.parametrize(
        ("enabled", "method"),
        [(True, "enable_automation"), (False, "disable_automation")],
    )
    async def test_set_automation_enabled(self, api, client, enabled, method):
        api._handle_event(
            snapshot(automations=[automation("x", not enabled), automation("y")])
        )
        listener = MagicMock()
        api.async_add_listener(listener, AUTOMATION_CONTEXT)
        switched = automation("x", enabled)
        setattr(client, method, AsyncMock(return_value=switched))
        assert await api.set_automation_enabled("x", enabled)
        getattr(client, method).assert_called_once_with("x")
        assert api.automations == [switched, automation("y")]
        assert listener.called

    async def test_set_automation_enabled_failed(self, api, client):
        automations = [automation("x")]
        api._handle_event(snapshot(automations=automations))
        client.disable_automation = AsyncMock(return_value=None)
        assert not await api.set_automation_enabled("x", False)
        assert api.automations == automations

    async def test_update_changed_updates_only_its_listeners(self, api):
        api._handle_event(snapshot(shutter("a")))
        update_listener = MagicMock()
        device_listener = MagicMock()
        api.async_add_listener(update_listener, UPDATE_CONTEXT)
        api.async_add_listener(device_listener, "a")
        api._handle_event(UpdateChanged(UpdateStatus("2.13.4", "2.14.0", 0.5)))
        assert update_listener.called
        assert not device_listener.called

    @pytest.mark.parametrize(
        ("status", "result"), [(UpdateStatus("2.13.4", "2.14.0"), True), (None, False)]
    )
    async def test_install_update(self, api, client, status, result):
        client.install_update = AsyncMock(return_value=status)
        assert await api.install_update() is result
        client.install_update.assert_called_once_with()

    async def test_now(self, api):
        assert api.now() == 1.5

    async def test_get_timezone(self, api):
        assert await api.get_timezone() == "Europe/Vienna"

    async def test_get_timezone_fallback(self, api, client):
        client.date_information.return_value = None
        assert await api.get_timezone() == "UTC"

    async def test_send_device_command_action(self, api, client):
        await api.send_device_command_action("id", Action.STOP)
        identifier, command = client.send_command.call_args.args
        assert identifier == "id"
        assert command.action == Action.STOP

    async def test_send_device_command_properties(self, api, client):
        await api.send_device_command_properties("id", {"target_position": 1})
        identifier, command = client.send_command.call_args.args
        assert identifier == "id"
        assert command.properties == {"target_position": 1}

    def test_command_exception_is_home_assistant_error(self):
        """Automations can only continue on errors of this type."""
        assert issubclass(CommandException, HomeAssistantError)

    async def test_send_device_command_failed(self, api, client):
        client.send_command.return_value = False
        with patch("custom_components.hella_onyx.api_connector.asyncio.sleep"):
            with pytest.raises(CommandException) as ex:
                await api.send_device_command_action("id", Action.CLOSE)
            assert ex.value.uuid == "id"
            with pytest.raises(CommandException):
                await api.send_device_command_properties("id", {})
        # one retry each, never more
        assert client.send_command.await_count == 4

    async def test_send_device_command_retries_once(self, api, client):
        client.send_command.side_effect = [False, True]
        with patch("custom_components.hella_onyx.api_connector.asyncio.sleep") as sleep:
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 2
        # same command both times, after a short jittered backoff
        first, second = client.send_command.await_args_list
        assert first.args == second.args
        delay = sleep.await_args.args[0]
        assert COMMAND_RETRY_DELAY_MIN <= delay <= COMMAND_RETRY_DELAY_MAX

    @pytest.mark.parametrize("error", [TimeoutError(), ClientConnectionError()])
    async def test_send_device_command_retries_on_error(self, api, client, error):
        client.send_command.side_effect = [error, True]
        with patch("custom_components.hella_onyx.api_connector.asyncio.sleep"):
            await api.send_device_command_properties("id", {"target_position": 1})
        assert client.send_command.await_count == 2

    async def test_send_device_command_error_twice(self, api, client):
        client.send_command.side_effect = TimeoutError()
        with (
            patch("custom_components.hella_onyx.api_connector.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert isinstance(ex.value.__cause__, TimeoutError)
        assert client.send_command.await_count == 2

    async def test_send_device_command_no_retry_on_success(self, api, client):
        with patch("custom_components.hella_onyx.api_connector.asyncio.sleep") as sleep:
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 1
        sleep.assert_not_called()

    async def test_send_device_command_retry_warns(self, api, client, caplog):
        client.send_command.side_effect = [False, True]
        with patch("custom_components.hella_onyx.api_connector.asyncio.sleep"):
            await api.send_device_command_action("id", Action.CLOSE)
        assert "retrying" in caplog.text
        assert "see the logged HTTP status" in caplog.text

    async def test_send_device_command_jitter_bounds(self, api, client):
        client.send_command.side_effect = [False, True]
        with (
            patch(f"{MODULE}.asyncio.sleep") as sleep,
            patch(f"{MODULE}.random.uniform", return_value=0.7) as uniform,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        uniform.assert_called_once_with(
            COMMAND_RETRY_DELAY_MIN, COMMAND_RETRY_DELAY_MAX
        )
        sleep.assert_awaited_once_with(0.7)

    async def test_send_device_command_sleeps_once_when_both_fail(self, api, client):
        client.send_command.return_value = False
        with (
            patch(f"{MODULE}.asyncio.sleep") as sleep,
            pytest.raises(CommandException),
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        sleep.assert_awaited_once()

    async def test_send_device_command_exception_message(self, api, client):
        client.send_command.return_value = False
        with (
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert str(ex.value) == ("ONYX_ACTION_ERROR: rejected by the ONYX API")

    async def test_send_device_command_stale_cause_is_dropped(self, api, client):
        """A timeout followed by a rejection is not the cause of the rejection."""
        client.send_command.side_effect = [TimeoutError(), False]
        with (
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert ex.value.__cause__ is None
        assert "rejected by the ONYX API" in str(ex.value)

    async def test_send_device_command_cancelled_attempt_propagates(self, api, client):
        client.send_command.side_effect = asyncio.CancelledError()
        with (
            patch(f"{MODULE}.asyncio.sleep") as sleep,
            pytest.raises(asyncio.CancelledError),
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 1
        sleep.assert_not_called()

    async def test_send_device_command_cancelled_backoff_propagates(self, api, client):
        client.send_command.return_value = False
        with (
            patch(f"{MODULE}.asyncio.sleep", side_effect=asyncio.CancelledError),
            pytest.raises(asyncio.CancelledError),
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 1

    @pytest.mark.parametrize(
        "error", [ValueError("bad"), json.JSONDecodeError("bad", "{", 0)]
    )
    async def test_send_device_command_value_error_not_retried(
        self, api, client, error
    ):
        client.send_command.side_effect = error
        with (
            patch(f"{MODULE}.asyncio.sleep") as sleep,
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 1
        sleep.assert_not_called()
        assert ex.value.__cause__ is error
        assert str(ex.value).startswith(f"ONYX_ACTION_ERROR: {type(error).__name__}")

    async def test_send_device_command_timeout(self, api, client, caplog):
        """A hanging attempt is cut after COMMAND_TIMEOUT and retried once."""

        async def hang(*args):
            await asyncio.Event().wait()

        client.send_command.side_effect = hang
        # fail fast instead of hanging if the attempt timeout is ever removed
        async with asyncio.timeout(2):
            with (
                patch(f"{MODULE}.COMMAND_TIMEOUT", 0.01),
                patch(f"{MODULE}.asyncio.sleep"),
                pytest.raises(CommandException) as ex,
            ):
                await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 2
        assert isinstance(ex.value.__cause__, TimeoutError)
        assert str(ex.value) == "ONYX_ACTION_ERROR: timed out after 0.01 s"
        assert caplog.text.count("retrying") == 1

    async def test_send_device_command_client_timeout_keeps_description(
        self, api, client
    ):
        """A TimeoutError raised by the client is not our attempt timeout."""
        client.send_command.side_effect = TimeoutError()
        with (
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert str(ex.value) == "ONYX_ACTION_ERROR: TimeoutError"

    async def test_send_device_command_invalid_url_not_retried(self, api, client):
        """InvalidURL is a ClientError and a ValueError; it is deterministic."""
        error = InvalidURL("bad url")
        client.send_command.side_effect = error
        with (
            patch(f"{MODULE}.asyncio.sleep") as sleep,
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert client.send_command.await_count == 1
        sleep.assert_not_called()
        assert ex.value.__cause__ is error

    def test_command_timeout_value(self):
        assert COMMAND_TIMEOUT == 10
