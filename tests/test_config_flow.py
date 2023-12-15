"""Test for the ONYX Config Flow."""
import pytest

from unittest.mock import patch, MagicMock

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)

from custom_components.hella_onyx.const import (
    CONF_FINGERPRINT,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
)
from custom_components.hella_onyx.config_flow import (
    OnyxFlowHandler,
    OnyxOptionsFlowHandler,
)


class TestOnyxFlowHandler:
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @pytest.mark.asyncio
    async def test_async_step_init_without_data(self, mock_async_show_form):
        config_flow = OnyxFlowHandler()
        await config_flow.async_step_init(None)
        assert mock_async_show_form.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_abort")
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_exists")
    @pytest.mark.asyncio
    async def test_async_step_init_with_data_exists(
        self, mock_async_exists, mock_async_abort, mock_async_create_entry
    ):
        config_flow = OnyxFlowHandler()
        await config_flow.async_step_init(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
                CONF_SCAN_INTERVAL: 10,
                CONF_MIN_DIM_DURATION: 0,
                CONF_MAX_DIM_DURATION: 100,
                CONF_FORCE_UPDATE: False,
            }
        )
        assert mock_async_exists.called
        assert mock_async_abort.called
        assert not mock_async_create_entry.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_abort")
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_exists")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @pytest.mark.asyncio
    async def test_async_step_init_with_data_invalid_creds(
        self,
        mock_async_verify_conn,
        mock_async_exists,
        mock_async_abort,
        mock_async_create_entry,
    ):
        mock_async_exists.return_value = False
        mock_async_verify_conn.return_value = False

        config_flow = OnyxFlowHandler()
        await config_flow.async_step_init(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
                CONF_SCAN_INTERVAL: 10,
                CONF_MIN_DIM_DURATION: 0,
                CONF_MAX_DIM_DURATION: 100,
                CONF_FORCE_UPDATE: False,
            }
        )
        assert mock_async_exists.called
        assert mock_async_verify_conn.called
        assert mock_async_abort.called
        assert not mock_async_create_entry.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_abort")
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_exists")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @pytest.mark.asyncio
    async def test_async_step_init_with_data(
        self,
        mock_async_verify_conn,
        mock_async_exists,
        mock_async_abort,
        mock_async_create_entry,
    ):
        mock_async_exists.return_value = False
        mock_async_verify_conn.return_value = True

        config_flow = OnyxFlowHandler()
        await config_flow.async_step_init(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
                CONF_SCAN_INTERVAL: 10,
                CONF_MIN_DIM_DURATION: 0,
                CONF_MAX_DIM_DURATION: 100,
                CONF_FORCE_UPDATE: False,
            }
        )
        assert mock_async_exists.called
        assert mock_async_verify_conn.called
        assert not mock_async_abort.called
        assert mock_async_create_entry.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_current_entries"
    )
    @pytest.mark.asyncio
    async def test_async_exists(
        self,
        mock_async_current_entries,
    ):
        entry = MagicMock()
        entry.data = {"fingerprint": "finger"}
        mock_async_current_entries.return_value = [entry]

        config_flow = OnyxFlowHandler()
        exists = await config_flow._async_exists("finger")
        assert exists
        assert mock_async_current_entries.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_current_entries"
    )
    @pytest.mark.asyncio
    async def test_async_exists_none(
        self,
        mock_async_current_entries,
    ):
        mock_async_current_entries.return_value = []

        config_flow = OnyxFlowHandler()
        exists = await config_flow._async_exists("finger")
        assert not exists
        assert mock_async_current_entries.called

    @patch("onyx_client.client.OnyxClient.verify")
    @pytest.mark.asyncio
    async def test_async_verify_conn(
        self,
        mock_verify,
    ):
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow._async_verify_conn("finger", "token")
        assert mock_verify.called


class TestOnyxOptionsFlowHandler:
    @pytest.mark.asyncio
    async def test_async_step_init_without_data(
        self,
    ):
        entry = MagicMock()
        value = {
            CONF_SCAN_INTERVAL: 10,
            CONF_MIN_DIM_DURATION: 0,
            CONF_MAX_DIM_DURATION: 100,
            CONF_FORCE_UPDATE: False,
        }
        entry.options.return_value = value
        options_flow = OnyxOptionsFlowHandler(entry)
        form = await options_flow.async_step_init()
        assert form is not None
        assert "title" not in form
        assert "min_dim_duration" in form["data_schema"].schema
        assert "scan_interval" in form["data_schema"].schema
        assert "force_update" in form["data_schema"].schema

    @pytest.mark.asyncio
    async def test_async_step_init_with_data(
        self,
    ):
        entry = MagicMock()
        entry.options.return_value = {
            CONF_SCAN_INTERVAL: 10,
            CONF_MIN_DIM_DURATION: 0,
            CONF_MAX_DIM_DURATION: 100,
            CONF_FORCE_UPDATE: False,
        }
        options_flow = OnyxOptionsFlowHandler(entry)
        user_input = {
            CONF_SCAN_INTERVAL: 100,
            CONF_MIN_DIM_DURATION: 10,
            CONF_MAX_DIM_DURATION: 10,
            CONF_FORCE_UPDATE: False,
        }
        form = await options_flow.async_step_init(user_input)
        assert form is not None
        assert form["title"] == ""
        assert form["data"] == user_input
