"""Test for the ONYX Config Flow."""

from unittest.mock import patch

import pytest
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)

from custom_components.hella_onyx import CONF_FINGERPRINT
from custom_components.hella_onyx.config_flow import OnyxFlowHandler


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
                CONF_FORCE_UPDATE: False,
            }
        )
        assert mock_async_exists.called
        assert mock_async_verify_conn.called
        assert not mock_async_abort.called
        assert mock_async_create_entry.called
