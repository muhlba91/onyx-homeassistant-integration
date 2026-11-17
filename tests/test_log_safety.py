"""Tests that the access token never reaches the log."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientConnectionError, ClientResponseError, RequestInfo
from homeassistant.helpers.update_coordinator import UpdateFailed
from multidict import CIMultiDict, CIMultiDictProxy
from onyx_client.enum.action import Action
from onyx_client.utils.sanitize import strip_credentials
from yarl import URL

from custom_components.hella_onyx import api_connector
from custom_components.hella_onyx.api_connector import APIConnector, CommandException
from custom_components.hella_onyx.configuration import Configuration

from .helpers import MODULE, FakeClient, shutter, snapshot

TOKEN = "s3cr3t-t0k3n-value"


def response_error(status=404) -> ClientResponseError:
    url = URL("https://api.hella.link/box/FINGERPRINT/api/v6/events?x=1")
    info = RequestInfo(
        url,
        "GET",
        CIMultiDictProxy(CIMultiDict({"Authorization": f"Bearer {TOKEN}"})),
        url,
    )
    return ClientResponseError(info, (), status=status, message="Not Found")


def test_configuration_repr_has_no_token():
    config = Configuration(1, 2, 3, 4, 5, 6, 7, "finger", TOKEN, None)
    assert TOKEN not in repr(config)
    assert TOKEN not in str(config)
    assert TOKEN not in f"{config!r}"


class TestStreamLogging:
    @pytest.fixture
    def config(self):
        yield Configuration(60, 1, 2, 3, 4, 5, 6, "finger", TOKEN, None)

    @pytest.fixture
    def client(self):
        yield FakeClient([snapshot(shutter("a"))])

    @pytest.fixture
    async def api(self, hass, config, client):
        api = APIConnector(hass, config)
        api.config_entry = MagicMock()
        api._APIConnector__client = client
        yield api
        await api._stop_stream()

    @pytest.mark.parametrize("status", [401, 403])
    async def test_rejected_stream_log_has_no_token(self, api, client, caplog, status):
        client.error = response_error(status)
        with caplog.at_level(logging.DEBUG):
            await api._async_update_data()
            await api._stream_task
        assert f"status={status}" in caplog.text
        assert TOKEN not in caplog.text
        assert "Authorization" not in caplog.text
        assert TOKEN not in repr(api.last_exception)
        assert TOKEN not in str(api.last_exception)

    async def test_failed_stream_log_has_no_token(self, api, client, caplog):
        client.error = ClientConnectionError(f"Bearer {TOKEN}")
        with (
            caplog.at_level(logging.DEBUG),
            patch(f"{MODULE}.async_call_later", MagicMock()),
        ):
            await api._async_update_data()
            await api._stream_task
        assert "event stream failed (ClientConnectionError Bearer ***)" in caplog.text
        assert "Traceback" not in caplog.text
        assert TOKEN not in caplog.text
        assert TOKEN not in repr(api.last_exception)
        assert isinstance(api.last_exception, UpdateFailed)
        assert str(api.last_exception) == "ClientConnectionError Bearer ***"

    async def test_unexpected_error_keeps_traceback(self, api, client, caplog):
        client.error = RuntimeError("boom")
        with (
            caplog.at_level(logging.DEBUG),
            patch(f"{MODULE}.async_call_later", MagicMock()),
        ):
            await api._async_update_data()
            await api._stream_task
        assert "Traceback" in caplog.text
        assert "RuntimeError: boom" in caplog.text
        # an unexpected error stays the original exception
        assert isinstance(api.last_exception, RuntimeError)
        assert str(api.last_exception) == "boom"

    async def test_failed_command_log_has_no_token(self, api, client, caplog):
        # the error as the client raises it: stripped of the request headers
        error = response_error(500)
        strip_credentials(error)
        client.send_command.side_effect = error
        with (
            caplog.at_level(logging.DEBUG),
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert "status=500" in caplog.text
        assert caplog.text.count("command errored") == 1
        assert TOKEN not in caplog.text
        assert TOKEN not in str(ex.value)
        assert TOKEN not in repr(ex.value.__cause__)
        assert "status=500" in str(ex.value)

    async def test_failed_command_with_unstripped_error_has_no_token(
        self, api, client, caplog
    ):
        client.send_command.side_effect = response_error(500)
        with (
            caplog.at_level(logging.DEBUG),
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException) as ex,
        ):
            await api.send_device_command_action("id", Action.CLOSE)
        assert TOKEN not in caplog.text
        assert TOKEN not in str(ex.value)

    async def test_rejected_command_message(self, api, client):
        client.send_command.return_value = False
        with (
            patch(f"{MODULE}.asyncio.sleep"),
            pytest.raises(CommandException, match="rejected by the ONYX API"),
        ):
            await api.send_device_command_action("id", Action.CLOSE)

    async def test_update_error_has_no_token(self, api, client):
        """The UpdateFailed handed to the coordinator, which HA logs."""
        client.error = response_error(401)
        with patch.object(
            api, "async_set_update_error", wraps=api.async_set_update_error
        ) as set_error:
            await api._async_update_data()
            await api._stream_task
        (error,) = set_error.call_args.args
        assert isinstance(error, UpdateFailed)
        assert "status=401" in str(error)
        assert TOKEN not in str(error) + repr(error)


def test_module_logger_masks_bearer_tokens(caplog):
    with caplog.at_level(logging.INFO):
        api_connector._LOGGER.info("request failed: Bearer %s", "x")
    assert "Bearer ***" in caplog.text
    assert "Bearer x" not in caplog.text
