"""Test for the ONYX API Connector."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.update_coordinator import UpdateFailed
from onyx_client.client import OnyxClient
from onyx_client.data.date_information import DateInformation
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
    Snapshot,
    UpdateChanged,
)
from onyx_client.utils.mapper import init_device

from custom_components.hella_onyx.api_connector import APIConnector, CommandException
from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.const import (
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

MODULE = "custom_components.hella_onyx.api_connector"


def shutter(identifier: str, position: int = 0):
    return init_device(
        identifier,
        {
            "name": identifier,
            "type": "rollershutter",
            "properties": {"actual_position": {"value": position, "maximum": 100}},
        },
    )


def snapshot(*devices):
    return Snapshot(
        {device.identifier: device for device in devices},
        {"group": Group("group", "Group", ["a"])},
        [],
        UpdateStatus("2.13.4"),
    )


class FakeClient:
    """A client streaming the given events, then staying connected."""

    def __init__(self, events=(), error=None):
        self.events = list(events)
        self.error = error
        self.verify = AsyncMock(return_value=VerifyResult.OK)
        self.resync = MagicMock()
        self.close = AsyncMock()
        self.now = MagicMock(return_value=1.5)
        self.send_command = AsyncMock(return_value=True)
        self.date_information = AsyncMock(
            return_value=DateInformation(0, "Europe/Vienna", 0)
        )

    async def stream(self):
        for event in self.events:
            yield event
        if self.error is not None:
            raise self.error
        await asyncio.Event().wait()


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
        now = api._last_event
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
        api.last_update_success = False
        listener = MagicMock()
        api.async_add_listener(listener, "a")
        api._handle_event(event)
        assert api.last_update_success
        listener.assert_called_once_with()

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
        api._last_event = 0
        api._check_stream(None)
        assert api.last_update_success

    async def test_resync_of_silent_stream_fails(self, api, client):
        await api._async_update_data()
        api._last_event = 0
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
        api._handle_event(snapshot(shutter("a")))
        groups = {"other": Group("other", "Other", [])}
        api._handle_event(GroupsChanged(groups))
        api._handle_event(AutomationsChanged(["automation"]))
        api._handle_event(UpdateChanged(UpdateStatus("2.14.0")))
        api._handle_event(Pulse(1.0))
        assert api.groups == groups
        assert api.data["automations"] == ["automation"]
        assert api.data["update"].current == "2.14.0"
        assert api.update_status is api.data["update"]

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

    async def test_send_device_command_failed(self, api, client):
        client.send_command.return_value = False
        with pytest.raises(CommandException) as ex:
            await api.send_device_command_action("id", Action.CLOSE)
        assert ex.value.uuid == "id"
        with pytest.raises(CommandException):
            await api.send_device_command_properties("id", {})
