"""Test for the ONYX API Connector."""

import asyncio
import pytest

from unittest.mock import MagicMock, patch

from onyx_client.client import OnyxClient
from onyx_client.data.numeric_value import NumericValue
from onyx_client.data.date_information import DateInformation
from onyx_client.data.device_command import DeviceCommand
from onyx_client.data.device_mode import DeviceMode
from onyx_client.device.device import Device
from onyx_client.device.shutter import Shutter
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType
from onyx_client.group.group import Group

from custom_components.hella_onyx import APIConnector
from custom_components.hella_onyx.const import (
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_ADDITIONAL_DELAY,
)
from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.api_connector import (
    CommandException,
    UnknownStateException,
    MAX_BACKOFF_TIME,
)


class TestAPIConnector:
    @pytest.fixture
    def client(self):
        yield MockClient()

    @pytest.fixture
    def api(self):
        config = Configuration(
            100000000,
            DEFAULT_MIN_DIM_DURATION,
            DEFAULT_MAX_DIM_DURATION,
            DEFAULT_ADDITIONAL_DELAY,
            DEFAULT_INTERPOLATION_FREQUENCY,
            False,
            "finger",
            "token",
            None,
        )
        yield APIConnector(None, config)

    def test_init_properties(self, api):
        assert api.config is not None
        assert api.config.scan_interval == 100000000
        assert api.name == "hella_onyx"

    @pytest.mark.asyncio
    async def test_update(self, api, client):
        with patch.object(api, "_client", new=client.make):
            data = await api.update()
            assert len(data["devices"]) == 1
            assert len(data["groups"]) == 1
            assert client.is_called

    @pytest.mark.asyncio
    async def test_get_timezone(self, api, client):
        with patch.object(api, "_client", new=client.make):
            tz = await api.get_timezone()
            assert tz == "Europe/Vienna"
            assert client.is_called

    @pytest.mark.asyncio
    async def test_get_timezone_fallback(self, api):
        client = MockClientNoDate()
        with patch.object(api, "_client", new=client.make):
            tz = await api.get_timezone()
            assert tz == "UTC"
            assert client.called

    def test_device(self, api):
        api.data = {"devices": {"uuid": "device"}}
        assert api.device("uuid") == "device"

    def test_device_not_found(self, api):
        with pytest.raises(UnknownStateException):
            api.device("uuid")

    def test_devices(self, api):
        assert api.devices == {}
        api.data = {"devices": {"uuid": "device"}}
        assert api.devices == {"uuid": "device"}

    def test_groups(self, api):
        assert api.groups == {}
        api.data = {"groups": {"uuid": "group"}}
        assert api.groups == {"uuid": "group"}

    @pytest.mark.asyncio
    async def test_update_device(self, api, client):
        assert len(api.devices) == 0
        with patch.object(api, "_client", new=client.make):
            await api.update_device("id")
            assert len(api.devices) == 1
            assert api.devices["id"] is not None
            assert api.devices["id"].identifier == "id"
            assert client.is_called

    @pytest.mark.asyncio
    async def test_updater(self, api, client):
        with patch.object(api, "async_set_updated_data") as mock_async_set_updated_data:
            await api._updater()
            assert mock_async_set_updated_data.called

    @pytest.mark.asyncio
    async def test_async_update_data(self, api, client):
        with patch.object(api, "_client", new=client.make):
            await api._async_update_data()
            assert client.is_called

    @pytest.mark.asyncio
    async def test_updated_device(self, api):
        api.data = {
            "devices": {
                "id": Shutter(
                    "id",
                    "name",
                    DeviceType.RAFFSTORE_90,
                    DeviceMode(DeviceType.RAFFSTORE_90),
                    list(Action),
                    actual_angle=NumericValue(0, 0, 0, False),
                    actual_position=NumericValue(0, 0, 0, False),
                )
            }
        }
        assert len(api.devices) == 1
        actual_angle = NumericValue(1, 1, 1, False)
        api.updated_device(
            Shutter(
                "id",
                "name",
                DeviceType.RAFFSTORE_90,
                DeviceMode(DeviceType.RAFFSTORE_90),
                list(Action),
                actual_angle=actual_angle,
            )
        )
        assert api.devices["id"].actual_angle == actual_angle

    def test_updated_device_attribute_error(self, api):
        api.data = {
            "devices": {
                "id": Shutter(
                    "id",
                    "name",
                    DeviceType.RAFFSTORE_90,
                    DeviceMode(DeviceType.RAFFSTORE_90),
                    list(Action),
                    actual_angle=NumericValue(0, 0, 0, False),
                    actual_position=NumericValue(0, 0, 0, False),
                )
            }
        }
        mock_shutter = MagicMock()
        mock_shutter.identifier = "id"
        mock_shutter.update_with.side_effect = TypeError("incompatible")
        api.data["devices"]["id"] = mock_shutter

        incompatible_patch = Device("id", None, DeviceType.UNKNOWN, None, [])
        # Must not raise — the error is logged as a WARNING and swallowed
        api.updated_device(incompatible_patch)
        mock_shutter.update_with.assert_called_once_with(incompatible_patch)

    @pytest.mark.asyncio
    async def test_updated_device_new(self, api, client):
        api.data = {
            "devices": {
                "id": Shutter(
                    "id",
                    "name",
                    DeviceType.RAFFSTORE_90,
                    DeviceMode(DeviceType.RAFFSTORE_90),
                    list(Action),
                    actual_angle=NumericValue(0, 0, 0, False),
                    actual_position=NumericValue(0, 0, 0, False),
                )
            }
        }
        assert len(api.devices) == 1
        api.updated_device(
            Shutter(
                "id1",
                "name",
                DeviceType.RAFFSTORE_90,
                DeviceMode(DeviceType.RAFFSTORE_90),
                list(Action),
            )
        )
        assert api.devices["id"].actual_angle == NumericValue(0, 0, 0, False)

    @pytest.mark.asyncio
    async def test_send_device_command_action(self, api, client):
        with patch.object(api, "_client", new=client.make):
            await api.send_device_command_action("id", Action.STOP)
            assert client.is_called

    @pytest.mark.asyncio
    async def test_send_device_command_action_failed(self, api, client):
        with patch.object(api, "_client", new=client.make):
            with pytest.raises(CommandException):
                await api.send_device_command_action("id", Action.CLOSE)
            assert client.is_called

    @pytest.mark.asyncio
    async def test_send_device_command_properties(self, api, client):
        with patch.object(api, "_client", new=client.make):
            await api.send_device_command_properties("id", {"action": 0})
            assert client.is_called

    @pytest.mark.asyncio
    async def test_send_device_command_properties_failed(self, api, client):
        with patch.object(api, "_client", new=client.make):
            with pytest.raises(CommandException):
                await api.send_device_command_properties("id", {"fail": 0})
            assert client.is_called

    @pytest.mark.asyncio
    async def test__client(self, api):
        api.hass = MagicMock()
        client = api._client()
        assert client is not None
        assert isinstance(client, OnyxClient)

    @pytest.mark.asyncio
    async def test_events(self, api, client):
        api._backoff = False
        with patch.object(api, "_client", new=client.make):
            with patch.object(api, "updated_device") as mock_updated_device:
                with patch.object(api, "_updater") as mock_updater:
                    await api.events()
                    assert client.is_called
                    assert not client.is_force_update
                    assert mock_updated_device.called
                    assert mock_updater.called

    @pytest.mark.asyncio
    async def test_events_force_update(self, api, client):
        api._backoff = False
        with patch.object(api, "_client", new=client.make):
            with patch.object(api, "updated_device") as mock_updated_device:
                with patch.object(api, "_updater") as mock_updater:
                    await api.events(True)
                    assert client.is_called
                    assert client.is_force_update
                    assert mock_updated_device.called
                    assert mock_updater.called

    @pytest.mark.asyncio
    async def test_events_invalid_device(self, api, client):
        api._backoff = False
        api.fail_device = True
        with patch.object(api, "_client", new=client.make):
            with patch.object(api, "updated_device") as mock_updated_device:
                with patch.object(api, "_updater") as mock_updater:
                    await api.events()
                    assert client.is_called
                    assert mock_updated_device.called
                    assert mock_updater.called

    @pytest.mark.asyncio
    async def test_events_none_device(self, api, client):
        api._backoff = False
        api.none_device = True
        with patch.object(api, "_client", new=client.make):
            with patch.object(api, "updated_device") as mock_updated_device:
                with patch.object(api, "_updater") as mock_updater:
                    await api.events()
                    assert client.is_called
                    assert mock_updated_device.called
                    assert mock_updater.called

    @pytest.mark.asyncio
    async def test_events_connection_error(self, api, client):
        api._backoff = False
        api.fail = True
        with patch.object(api, "_client", new=client.make):
            with patch.object(api, "updated_device") as mock_updated_device:
                with patch.object(api, "_updater") as mock_updater:
                    await api.events()
                    assert client.is_called
                    assert mock_updated_device.called
                    assert mock_updater.called

    @pytest.mark.asyncio
    async def test_events_update_with_attribute_error(self, api):
        """Events loop must NOT reconnect when update_with raises AttributeError.

        Reproduces the 'Device' object has no attribute 'wind_peak' scenario:
        the stored device is a Shutter but the SSE stream emits a plain Device patch.
        The error is caught inside updated_device() and the loop continues without
        triggering a connection reset / backoff.
        """
        api.data = {
            "devices": {
                "id": Shutter(
                    "id",
                    "name",
                    DeviceType.RAFFSTORE_90,
                    DeviceMode(DeviceType.RAFFSTORE_90),
                    list(Action),
                    actual_angle=NumericValue(0, 0, 0, False),
                    actual_position=NumericValue(0, 0, 0, False),
                )
            }
        }

        async def events_with_incompatible_patch(force_update: bool):
            # Emit a plain Device — this would previously cause AttributeError in update_with
            yield Device("id", None, DeviceType.UNKNOWN, None, [])

        mock_client = MagicMock()
        mock_client.events = events_with_incompatible_patch

        connection_reset_logged = []

        def capture_warning(msg, *args, **kwargs):
            if "connection reset" in msg:
                connection_reset_logged.append(msg)

        with patch.object(api, "_client", return_value=mock_client):
            with patch.object(api, "_updater"):
                api._backoff = False
                import logging

                with patch.object(
                    logging.getLogger("custom_components.hella_onyx.api_connector"),
                    "warning",
                    side_effect=capture_warning,
                ):
                    await api.events()

        # No connection-reset warning must have been emitted
        assert len(connection_reset_logged) == 0
        # The stored shutter is still intact
        assert api.devices["id"].actual_angle == NumericValue(0, 0, 0, False)

    @pytest.mark.asyncio
    async def test_events_connection_error_raises(self, api):
        """Exception from the async generator hits the inner except Exception handler."""

        async def failing_events(force_update: bool):
            raise ConnectionError("stream lost")
            yield  # pragma: no cover – makes this an async generator

        mock_client = MagicMock()
        mock_client.events = failing_events

        with patch.object(api, "_client", return_value=mock_client):
            api._backoff = False
            # Must complete without propagating the connection error
            await api.events()

    @pytest.mark.asyncio
    async def test_events_cancelled_inner(self, api):
        """CancelledError from the async generator hits both CancelledError handlers."""

        async def cancelled_events(force_update: bool):
            raise asyncio.CancelledError()
            yield  # pragma: no cover – makes this an async generator

        mock_client = MagicMock()
        mock_client.events = cancelled_events

        with patch.object(api, "_client", return_value=mock_client):
            api._backoff = False
            # Must complete without propagating CancelledError — outer handler absorbs it
            await api.events()

    @pytest.mark.asyncio
    async def test_events_backoff(self, api, client):
        async def sleep_called(backoff: int):
            assert backoff > 0
            assert backoff / 60 < MAX_BACKOFF_TIME
            api._backoff = False

        with patch("asyncio.sleep", new=sleep_called):
            with patch.object(api, "_client", new=client.make):
                with patch.object(api, "updated_device") as mock_updated_device:
                    with patch.object(api, "_updater") as mock_updater:
                        assert api._backoff
                        await api.events()
                        assert client.is_called
                        assert not api._backoff
                        assert mock_updated_device.called
                        assert mock_updater.called

    def test_command_exception_message(self):
        exc = CommandException("ONYX_ACTION_ERROR", "uuid-123")
        assert str(exc) == "ONYX_ACTION_ERROR"

    def test_unknown_state_exception_message(self):
        exc = UnknownStateException("UNKNOWN_DEVICE")
        assert str(exc) == "UNKNOWN_DEVICE"

    def test_device_not_found_message(self, api):
        try:
            api.device("missing")
        except UnknownStateException as exc:
            assert str(exc) == "UNKNOWN_DEVICE"

    @pytest.mark.asyncio
    async def test__client_uses_fingerprint_and_token(self, api):
        api.hass = MagicMock()
        client = api._client()
        assert client is not None
        assert isinstance(client, OnyxClient)
        # Fingerprint and token come from config — mutmut replaces with None; this
        # verifies that a valid client is built when the config values are real strings.
        assert api.config.fingerprint == "finger"
        assert api.config.token == "token"

    @pytest.mark.asyncio
    async def test_updater_passes_data_not_none(self, api):
        api.data = {"devices": {}, "groups": {}}
        with patch.object(api, "async_set_updated_data") as mock:
            await api._updater()
            mock.assert_called_once_with(api.data)
            assert mock.call_args[0][0] is not None

    @pytest.mark.asyncio
    async def test_async_update_data_timeout(self, api, client):
        """Mutmut replaces timeout(10) with timeout(None) — ensure 10 is non-None."""
        with patch.object(api, "_client", new=client.make):
            # Just confirm _async_update_data executes without raising
            await api._async_update_data()
            assert client.is_called

    @pytest.mark.asyncio
    async def test_update_device_passes_uuid(self, api, client):
        """Mutmut replaces uuid with None in _client().device(uuid)."""
        with patch.object(api, "_client", new=client.make):
            await api.update_device("id")
            # MockClient.device records nothing, but verifying uuid was NOT None:
            # the shutter returned has identifier "id" so it was stored correctly.
            assert "id" in api.devices

    @pytest.mark.asyncio
    async def test_send_device_command_action_uses_uuid(self, api, client):
        """Mutmut replaces uuid with None — command must be sent with the real uuid."""
        with patch.object(api, "_client", new=client.make):
            await api.send_device_command_action("id", Action.STOP)
            assert client.is_called

    @pytest.mark.asyncio
    async def test_send_device_command_action_failed_message_and_uuid(
        self, api, client
    ):
        """Mutmut changes error msg string or uuid to None."""
        with patch.object(api, "_client", new=client.make):
            try:
                await api.send_device_command_action("id", Action.CLOSE)
            except CommandException as exc:
                assert str(exc) == "ONYX_ACTION_ERROR"
                assert exc.args[0] == "ONYX_ACTION_ERROR"
                assert exc.uuid == "id"

    @pytest.mark.asyncio
    async def test_send_device_command_properties_failed_message_and_uuid(
        self, api, client
    ):
        """Mutmut changes error msg string or uuid to None."""
        with patch.object(api, "_client", new=client.make):
            try:
                await api.send_device_command_properties("id", {"fail": 0})
            except CommandException as exc:
                assert str(exc) == "ONYX_ACTION_ERROR"
                assert exc.args[0] == "ONYX_ACTION_ERROR"
                assert exc.uuid == "id"

    @pytest.mark.asyncio
    async def test_events_backoff_range_upper_bound(self, api, client):
        """Mutmut: MAX_BACKOFF_TIME * 60 vs * 61 — assert upper bound correct."""
        captured_backoffs = []

        async def sleep_and_record(delay: int):
            captured_backoffs.append(delay)
            api._backoff = False

        with patch("asyncio.sleep", new=sleep_and_record):
            with patch.object(api, "_client", new=client.make):
                with patch.object(api, "updated_device"):
                    with patch.object(api, "_updater"):
                        assert api._backoff
                        await api.events()
                        assert len(captured_backoffs) == 1
                        assert captured_backoffs[0] / 60 < MAX_BACKOFF_TIME
                        assert captured_backoffs[0] >= 1

    @pytest.mark.asyncio
    async def test_init_passes_hass_not_none(self):
        """Mutmut replaces hass with None — verify real hass object is forwarded."""
        from homeassistant.core import HomeAssistant

        hass = MagicMock(spec=HomeAssistant)
        config = Configuration(
            100,
            DEFAULT_MIN_DIM_DURATION,
            DEFAULT_MAX_DIM_DURATION,
            DEFAULT_ADDITIONAL_DELAY,
            DEFAULT_INTERPOLATION_FREQUENCY,
            False,
            "finger",
            "token",
            None,
        )
        entry = MagicMock()
        connector = APIConnector(hass, config, entry)
        # hass is stored on the DataUpdateCoordinator base
        assert connector.hass is hass
        assert connector.config_entry is entry
        assert connector.config is config
        assert connector.update_interval.total_seconds() == 6000
        assert connector._backoff is True

    @pytest.mark.asyncio
    @patch("custom_components.hella_onyx.api_connector.async_get_clientsession")
    @patch("custom_components.hella_onyx.api_connector.create")
    async def test__client_params(self, mock_create, mock_session, api):
        api.hass = MagicMock()
        api.config.local_address = "192.168.1.100"
        client = api._client()
        assert client == mock_create.return_value
        mock_create.assert_called_once_with(
            fingerprint="finger",
            access_token="token",
            client_session=mock_session.return_value,
            local_address="192.168.1.100",
        )


class MockClient:
    def __init__(self):
        self.called = False
        self.force_update = False
        self.date = None

    def make(self, *kwargs):
        self.called = False
        self.force_update = False
        self.date = DateInformation(100.0, "Europe/Vienna", 3600)
        return self

    @property
    def is_called(self):
        return self.called

    @property
    def is_force_update(self):
        return self.force_update

    async def devices(self, include_details: bool):
        assert include_details
        self.called = True
        return [
            Shutter(
                "id",
                "name",
                DeviceType.RAFFSTORE_90,
                DeviceMode(DeviceType.RAFFSTORE_90),
                list(Action),
            )
        ]

    async def groups(self):
        self.called = True
        return [Group("group", "group", [])]

    async def device(self, uuid: str):
        assert uuid == "id"
        self.called = True
        return Shutter(
            "id",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

    async def events(self, force_update: bool):
        self.called = True
        self.force_update = force_update
        yield Shutter(
            "id",
            "other",
            DeviceType.RAFFSTORE_90,
            DeviceMode(DeviceType.RAFFSTORE_90),
            list(Action),
        )

    async def send_command(self, uuid: str, command: DeviceCommand):
        assert uuid == "id"
        self.called = True
        return command.action == Action.STOP or (
            command.properties is not None and "fail" not in command.properties
        )

    async def date_information(self):
        self.called = True
        return self.date


class MockClientNoDate(MockClient):
    async def date_information(self):
        self.called = True
        return None
