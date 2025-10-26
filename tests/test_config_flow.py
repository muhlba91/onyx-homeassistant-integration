"""Test for the ONYX Config Flow."""

import pytest

from unittest.mock import patch, MagicMock
from aioresponses import aioresponses

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CODE,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)
from homeassistant.config_entries import ConfigEntry

from custom_components.hella_onyx.const import (
    CONF_FINGERPRINT,
    CONF_INTERPOLATION_FREQUENCY,
    CONF_LOCAL_ADDRESS,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    CONF_ADDITIONAL_DELAY,
)
from custom_components.hella_onyx.config_flow import (
    OnyxFlowHandler,
    OnyxOptionsFlowHandler,
)

from onyx_client.utils.const import API_URL


class TestOnyxFlowHandler:
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_without_data(
        self, mock_async_step_options, mock_async_show_form
    ):
        config_flow = OnyxFlowHandler()
        await config_flow.async_step_user(None)
        assert mock_async_show_form.called
        assert not mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_data_exists(
        self,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
        mock_async_step_options,
    ):
        mock_async_verify_conn.return_value = True
        config_flow = OnyxFlowHandler()
        await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
            }
        )
        assert mock_async_abort_entries_match.called
        assert mock_async_verify_conn.called
        assert mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_data_invalid_creds(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = False

        config_flow = OnyxFlowHandler()
        await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
            }
        )
        assert mock_async_verify_conn.called
        assert not mock_async_abort_entries_match.called
        assert not mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_data(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True

        config_flow = OnyxFlowHandler()
        await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
            }
        )
        assert mock_async_abort_entries_match.called
        assert mock_async_verify_conn.called
        assert mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_data_and_local_address(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True

        config_flow = OnyxFlowHandler()
        await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
                CONF_LOCAL_ADDRESS: "localhost",
            }
        )
        assert mock_async_abort_entries_match.called
        assert mock_async_verify_conn.called
        assert mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_code(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        with aioresponses() as mock_response:
            mock_response.post(
                f"{API_URL}/authorize",
                status=200,
                payload={
                    "fingerprint": "finger",
                    "token": "token",
                },
            )

            config_flow = OnyxFlowHandler()
            config_flow.hass = MagicMock()
            await config_flow.async_step_user(
                {
                    CONF_CODE: "code",
                }
            )
            assert mock_async_abort_entries_match.called
            assert mock_async_verify_conn.called
            assert mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_code_and_local_address(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        with aioresponses() as mock_response:
            mock_response.post(
                "https://localhost/api/v3/authorize",
                status=200,
                payload={
                    "fingerprint": "finger",
                    "token": "token",
                },
            )

            config_flow = OnyxFlowHandler()
            config_flow.hass = MagicMock()
            await config_flow.async_step_user(
                {
                    CONF_CODE: "code",
                    CONF_LOCAL_ADDRESS: "localhost",
                }
            )
            assert mock_async_abort_entries_match.called
            assert mock_async_verify_conn.called
            assert mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @pytest.mark.asyncio
    async def test_async_step_user_with_invalid_code(
        self,
        mock_async_show_form,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        with aioresponses() as mock_response:
            mock_response.post(
                f"{API_URL}/authorize",
                status=400,
            )

            config_flow = OnyxFlowHandler()
            config_flow.hass = MagicMock()
            await config_flow.async_step_user(
                {
                    CONF_CODE: "code",
                }
            )
            assert not mock_async_abort_entries_match.called
            assert not mock_async_verify_conn.called
            assert not mock_async_step_options.called
            assert mock_async_show_form.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_entry(
        self,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True

        config_flow = OnyxFlowHandler()
        config_flow._entry = ConfigEntry(
            version=2,
            minor_version=1,
            domain="ONYX",
            title="finger",
            data={},
            source="",
            unique_id="onyx",
            options={},
            discovery_keys={},
        )
        config_flow.hass = MagicMock()
        await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "finger",
                CONF_ACCESS_TOKEN: "token",
            }
        )
        assert not mock_async_abort_entries_match.called
        assert config_flow.hass.config_entries.async_update_entry.called
        assert mock_async_verify_conn.called
        assert not mock_async_step_options.called

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_with_entry_no_data(
        self,
        mock_async_step_options,
        mock_async_abort_entries_match,
    ):
        config_flow = OnyxFlowHandler()
        config_flow._entry = ConfigEntry(
            version=2,
            minor_version=1,
            domain="ONYX",
            title="finger",
            data={},
            source="",
            unique_id="onyx",
            options={},
            discovery_keys={},
        )
        await config_flow.async_step_user()
        assert not mock_async_abort_entries_match.called
        assert not mock_async_step_options.called

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @pytest.mark.asyncio
    async def test_async_step_options_without_data(
        self, mock_async_create_entry, mock_async_step_options
    ):
        config_flow = OnyxFlowHandler()
        await config_flow.async_step_options(None)
        assert not mock_async_create_entry.called
        assert mock_async_step_options.called

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @pytest.mark.asyncio
    async def test_async_step_options_with_data(
        self, mock_async_create_entry, mock_async_step_options
    ):
        config_flow = OnyxFlowHandler()
        config_flow._data = {CONF_FINGERPRINT: "finger"}
        await config_flow.async_step_options(
            {
                CONF_LOCAL_ADDRESS: None,
                CONF_SCAN_INTERVAL: 60,
                CONF_MIN_DIM_DURATION: 0,
                CONF_MAX_DIM_DURATION: 2000,
                CONF_ADDITIONAL_DELAY: 1000,
                CONF_FORCE_UPDATE: True,
                CONF_INTERPOLATION_FREQUENCY: 5000,
            }
        )
        assert mock_async_create_entry.called
        assert not mock_async_step_options.called

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
    )
    @pytest.mark.asyncio
    async def test_async_step_options_with_data_and_local_address(
        self, mock_async_create_entry, mock_async_step_options
    ):
        config_flow = OnyxFlowHandler()
        config_flow._data = {CONF_FINGERPRINT: "finger"}
        await config_flow.async_step_options(
            {
                CONF_LOCAL_ADDRESS: "192.168.1.1",
                CONF_SCAN_INTERVAL: 60,
                CONF_MIN_DIM_DURATION: 0,
                CONF_MAX_DIM_DURATION: 2000,
                CONF_ADDITIONAL_DELAY: 1000,
                CONF_FORCE_UPDATE: True,
                CONF_INTERPOLATION_FREQUENCY: 5000,
            }
        )
        assert mock_async_create_entry.called
        assert not mock_async_step_options.called

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_user")
    @pytest.mark.asyncio
    async def test_async_step_reauth(self, mock_async_step_user):
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        config_flow.context = {"entry_id": "finger"}
        await config_flow.async_step_reauth({})
        assert mock_async_step_user.called

    @patch("onyx_client.client.OnyxClient.verify")
    @pytest.mark.asyncio
    async def test_async_verify_conn(
        self,
        mock_verify,
    ):
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow._async_verify_conn("finger", "token", None)
        assert mock_verify.called

    @patch("onyx_client.client.OnyxClient.verify")
    @pytest.mark.asyncio
    async def test_async_verify_conn_local_address(
        self,
        mock_verify,
    ):
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow._async_verify_conn("finger", "token", "192.168.1.1")
        assert mock_verify.called


class TestOnyxOptionsFlowHandler:
    @patch("homeassistant.core.HomeAssistant")
    @pytest.mark.asyncio
    async def test_async_step_init_without_data(
        self,
        mock_hass,
    ):
        entry = MagicMock()
        value = {
            CONF_SCAN_INTERVAL: 10,
            CONF_MIN_DIM_DURATION: 0,
            CONF_MAX_DIM_DURATION: 100,
            CONF_FORCE_UPDATE: False,
            CONF_INTERPOLATION_FREQUENCY: 5000,
        }
        entry.options.return_value = value
        options_flow = OnyxOptionsFlowHandler()
        options_flow.hass = mock_hass
        mock_hass.config_entries.async_get_entry.return_value = entry
        form = await options_flow.async_step_init()
        assert form is not None
        assert "title" not in form
        assert "min_dim_duration" in form["data_schema"].schema
        assert "additional_delay" in form["data_schema"].schema
        assert "scan_interval" in form["data_schema"].schema
        assert "force_update" in form["data_schema"].schema

    @patch("homeassistant.core.HomeAssistant")
    @pytest.mark.asyncio
    async def test_async_step_init_with_data(
        self,
        mock_hass,
    ):
        entry = MagicMock()
        entry.options.return_value = {
            CONF_SCAN_INTERVAL: 10,
            CONF_MIN_DIM_DURATION: 0,
            CONF_MAX_DIM_DURATION: 100,
            CONF_FORCE_UPDATE: False,
            CONF_INTERPOLATION_FREQUENCY: 5000,
        }
        options_flow = OnyxOptionsFlowHandler()
        options_flow.hass = mock_hass
        user_input = {
            CONF_SCAN_INTERVAL: 100,
            CONF_MIN_DIM_DURATION: 10,
            CONF_MAX_DIM_DURATION: 10,
            CONF_ADDITIONAL_DELAY: 10,
            CONF_FORCE_UPDATE: False,
        }
        mock_hass.config_entries.async_get_entry.return_value = entry
        form = await options_flow.async_step_init(user_input)
        assert form is not None
        assert form["title"] != ""
        assert form["data"] == user_input
