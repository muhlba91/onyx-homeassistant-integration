"""Test for the ONYX Config Flow."""

import pytest

from unittest.mock import AsyncMock, MagicMock, patch, ANY

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
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_ADDITIONAL_DELAY,
    DEFAULT_INTERPOLATION_FREQUENCY,
    MIN_DIM_DURATION,
    MAX_DIM_DURATION,
    MIN_ADDITIONAL_DELAY,
    MAX_ADDITIONAL_DELAY,
    MIN_INTERPOLATION_FREQUENCY,
    MAX_INTERPOLATION_FREQUENCY,
)
from custom_components.hella_onyx.config_flow import (
    OnyxFlowHandler,
    OnyxOptionsFlowHandler,
    _get_options_schema,
)


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
        assert config_flow._data == {}
        assert config_flow._options == {}
        assert config_flow._entry is None
        config_flow.hass = MagicMock()
        await config_flow.async_step_user()
        assert mock_async_show_form.called
        assert not mock_async_step_options.called
        _, kwargs = mock_async_show_form.call_args
        assert kwargs["step_id"] == "user"
        schema = kwargs["data_schema"].schema
        assert CONF_FINGERPRINT in schema
        assert CONF_ACCESS_TOKEN in schema
        assert CONF_CODE in schema
        assert CONF_LOCAL_ADDRESS in schema

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
        mock_async_verify_conn.assert_called_once_with("finger", "token", None)
        assert not mock_async_abort_entries_match.called
        assert not mock_async_step_options.called
        assert config_flow._data == {}

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
        mock_async_abort_entries_match.assert_called_once_with(
            {CONF_FINGERPRINT: "finger"}
        )
        assert mock_async_verify_conn.called
        mock_async_verify_conn.assert_called_once_with("finger", "token", "localhost")
        assert mock_async_step_options.called
        assert config_flow._data == {
            CONF_FINGERPRINT: "finger",
            CONF_ACCESS_TOKEN: "token",
        }
        assert config_flow._options[CONF_LOCAL_ADDRESS] == "localhost"

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @patch("custom_components.hella_onyx.config_flow.authorize")
    @pytest.mark.asyncio
    async def test_async_step_user_with_code(
        self,
        mock_authorize,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        mock_auth_config = MagicMock()
        mock_auth_config.fingerprint = "finger"
        mock_auth_config.access_token = "token"
        mock_authorize.return_value = mock_auth_config

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
        mock_authorize.assert_called_once_with(
            "code",
            client_session=ANY,
            local_address=None,
        )
        assert config_flow._data[CONF_FINGERPRINT] == "finger"
        assert config_flow._data[CONF_ACCESS_TOKEN] == "token"

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @patch("custom_components.hella_onyx.config_flow.authorize")
    @pytest.mark.asyncio
    async def test_async_step_user_with_code_and_local_address(
        self,
        mock_authorize,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        mock_auth_config = MagicMock()
        mock_auth_config.fingerprint = "finger"
        mock_auth_config.access_token = "token"
        mock_authorize.return_value = mock_auth_config

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
        assert config_flow._data[CONF_FINGERPRINT] == "finger"
        assert config_flow._data[CONF_ACCESS_TOKEN] == "token"
        assert CONF_CODE not in config_flow._data

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
    @patch("custom_components.hella_onyx.config_flow.authorize")
    @pytest.mark.asyncio
    async def test_async_step_user_with_invalid_code(
        self,
        mock_authorize,
        mock_async_show_form,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        mock_async_verify_conn.return_value = True
        mock_authorize.return_value = None

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
        _, kwargs = mock_async_show_form.call_args
        assert kwargs["errors"] == {CONF_CODE: "invalid_code"}

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
            subentries_data={},
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
            subentries_data={},
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
        config_flow._options = {CONF_LOCAL_ADDRESS: "192.168.1.99"}
        await config_flow.async_step_options(None)
        assert not mock_async_create_entry.called
        assert mock_async_step_options.called
        kwargs = mock_async_step_options.call_args.kwargs
        assert kwargs["step_id"] == "options"
        schema_keys = {k.schema: k for k in kwargs["data_schema"].schema.keys()}
        assert CONF_SCAN_INTERVAL in schema_keys
        assert CONF_LOCAL_ADDRESS in schema_keys
        assert schema_keys[CONF_LOCAL_ADDRESS].default() == "192.168.1.99"
        assert CONF_ADDITIONAL_DELAY in schema_keys
        assert CONF_MIN_DIM_DURATION in schema_keys
        assert CONF_MAX_DIM_DURATION in schema_keys
        assert CONF_INTERPOLATION_FREQUENCY in schema_keys
        assert CONF_FORCE_UPDATE in schema_keys
        assert kwargs["errors"] == {}

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
        entry_kwargs = mock_async_create_entry.call_args.kwargs
        assert entry_kwargs["title"] == "finger"
        assert entry_kwargs["data"] == {CONF_FINGERPRINT: "finger"}
        assert entry_kwargs["options"][CONF_SCAN_INTERVAL] == 60
        assert entry_kwargs["options"][CONF_MIN_DIM_DURATION] == 0
        assert entry_kwargs["options"][CONF_MAX_DIM_DURATION] == 2000
        assert entry_kwargs["options"][CONF_ADDITIONAL_DELAY] == 1000
        assert entry_kwargs["options"][CONF_FORCE_UPDATE] is True
        assert entry_kwargs["options"][CONF_INTERPOLATION_FREQUENCY] == 5000
        assert entry_kwargs["options"][CONF_LOCAL_ADDRESS] is None

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
        entry_kwargs = mock_async_create_entry.call_args.kwargs
        assert entry_kwargs["title"] == "finger"
        assert entry_kwargs["data"] == {CONF_FINGERPRINT: "finger"}
        assert entry_kwargs["options"][CONF_LOCAL_ADDRESS] == "192.168.1.1"
        assert entry_kwargs["options"][CONF_SCAN_INTERVAL] == 60
        assert entry_kwargs["options"][CONF_FORCE_UPDATE] is True

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_user")
    @pytest.mark.asyncio
    async def test_async_step_reauth(self, mock_async_step_user):
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        config_flow.context = {"entry_id": "finger"}
        await config_flow.async_step_reauth({})
        assert mock_async_step_user.called
        config_flow.hass.config_entries.async_get_entry.assert_called_once_with(
            "finger"
        )
        assert (
            config_flow._entry
            == config_flow.hass.config_entries.async_get_entry.return_value
        )

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @pytest.mark.asyncio
    async def test_async_step_user_reauth_updates_entry_and_aborts(
        self,
        mock_async_verify_conn,
    ):
        mock_async_verify_conn.return_value = True
        config_flow = OnyxFlowHandler()
        mock_entry = MagicMock()
        mock_entry.entry_id = "entry_123"
        config_flow.hass = MagicMock()
        config_flow._entry = mock_entry
        config_flow.context = {"entry_id": "entry_123"}

        result = await config_flow.async_step_user(
            {
                CONF_FINGERPRINT: "new_fp",
                CONF_ACCESS_TOKEN: "new_tok",
                CONF_LOCAL_ADDRESS: "192.168.1.5",
            }
        )
        assert result["type"] == "abort"
        assert result["reason"] == "reauth_successful"
        config_flow.hass.config_entries.async_update_entry.assert_called_once_with(
            mock_entry,
            data={CONF_FINGERPRINT: "new_fp", CONF_ACCESS_TOKEN: "new_tok"},
            options={CONF_LOCAL_ADDRESS: "192.168.1.5"},
        )
        config_flow.hass.async_create_task.assert_called_once()
        config_flow.hass.config_entries.async_reload.assert_called_once_with(
            "entry_123"
        )

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

    @patch("custom_components.hella_onyx.config_flow.create")
    @pytest.mark.asyncio
    async def test_async_verify_conn_passes_fingerprint_not_none(self, mock_create):
        """Mutmut: fingerprint=fingerprint -> fingerprint=None."""
        mock_client = MagicMock()
        mock_client.verify = AsyncMock(return_value=True)
        mock_create.return_value = mock_client

        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow._async_verify_conn("finger", "token", None)

        _, kwargs = mock_create.call_args
        assert kwargs["fingerprint"] == "finger"
        assert kwargs["fingerprint"] is not None

    @patch("custom_components.hella_onyx.config_flow.async_get_clientsession")
    @patch("custom_components.hella_onyx.config_flow.create")
    @pytest.mark.asyncio
    async def test_async_verify_conn_passes_client_session_not_none(
        self, mock_create, mock_session
    ):
        """Mutmut: client_session=... -> client_session=None."""
        mock_client = MagicMock()
        mock_client.verify = AsyncMock(return_value=True)
        mock_create.return_value = mock_client

        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow._async_verify_conn("finger", "token", "192.168.1.1")

        mock_session.assert_called_once_with(config_flow.hass, False)
        _, kwargs = mock_create.call_args
        assert kwargs["access_token"] == "token"
        assert kwargs["local_address"] == "192.168.1.1"
        assert kwargs["client_session"] == mock_session.return_value

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_abort_entries_match"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_options"
    )
    @patch("custom_components.hella_onyx.config_flow.async_get_clientsession")
    @patch("custom_components.hella_onyx.config_flow.authorize")
    @pytest.mark.asyncio
    async def test_async_step_user_with_code_passes_client_session_not_none(
        self,
        mock_authorize,
        mock_session,
        mock_async_step_options,
        mock_async_verify_conn,
        mock_async_abort_entries_match,
    ):
        """Mutmut: client_session=... -> client_session=None in authorize call."""
        mock_async_verify_conn.return_value = True
        mock_auth_config = MagicMock()
        mock_auth_config.fingerprint = "finger"
        mock_auth_config.access_token = "token"
        mock_authorize.return_value = mock_auth_config

        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow.async_step_user(
            {CONF_CODE: "code", CONF_LOCAL_ADDRESS: "192.168.1.1"}
        )

        mock_session.assert_called_with(config_flow.hass, False)
        args, kwargs = mock_authorize.call_args
        assert args[0] == "code"
        assert kwargs["local_address"] == "192.168.1.1"
        assert kwargs["client_session"] == mock_session.return_value

    @patch(
        "custom_components.hella_onyx.config_flow.OnyxFlowHandler._async_verify_conn"
    )
    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form")
    @pytest.mark.asyncio
    async def test_async_step_user_invalid_conn_sets_error_value(
        self,
        mock_async_show_form,
        mock_async_verify_conn,
    ):
        """Mutmut: errors[CONF_ACCESS_TOKEN] = 'invalid_connection_data' -> None."""
        mock_async_verify_conn.return_value = False

        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        await config_flow.async_step_user(
            {CONF_FINGERPRINT: "finger", CONF_ACCESS_TOKEN: "token"}
        )
        _, kwargs = mock_async_show_form.call_args
        assert kwargs["errors"][CONF_ACCESS_TOKEN] == "invalid_connection_data"

    @pytest.mark.asyncio
    async def test_async_step_options_initialises_options_as_dict(self):
        """Mutmut: options = {} -> options = None — ensures dict is used."""

        @patch(
            "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_show_form"
        )
        @patch(
            "custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_create_entry"
        )
        async def _run(mock_create, mock_show):
            config_flow = OnyxFlowHandler()
            config_flow._data = {CONF_FINGERPRINT: "finger"}
            # Pass user_input with no local_address so options dict is populated
            await config_flow.async_step_options(
                {
                    CONF_LOCAL_ADDRESS: None,
                    CONF_SCAN_INTERVAL: 60,
                    CONF_MIN_DIM_DURATION: 0,
                    CONF_MAX_DIM_DURATION: 2000,
                    CONF_ADDITIONAL_DELAY: 0,
                    CONF_FORCE_UPDATE: False,
                    CONF_INTERPOLATION_FREQUENCY: 5000,
                }
            )
            assert mock_create.called
            entry_kwargs = mock_create.call_args.kwargs
            # options must be a dict, not None
            assert isinstance(entry_kwargs["options"], dict)

        await _run()

    @patch("custom_components.hella_onyx.config_flow.OnyxFlowHandler.async_step_user")
    @pytest.mark.asyncio
    async def test_async_step_reauth_forwards_data_not_none(self, mock_async_step_user):
        """Mutmut: async_step_user(data) -> async_step_user(None)."""
        config_flow = OnyxFlowHandler()
        config_flow.hass = MagicMock()
        config_flow.context = {"entry_id": "eid"}
        data = {CONF_FINGERPRINT: "fp", CONF_ACCESS_TOKEN: "tok"}
        await config_flow.async_step_reauth(data)
        mock_async_step_user.assert_called_once_with(data)
        assert mock_async_step_user.call_args[0][0] is not None


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


class TestGetOptionsSchema:
    def test_get_options_schema_defaults_and_selectors(self):
        schema = _get_options_schema(None)
        fields = schema.schema

        # Map markers to strings
        field_map = {k.schema: (k, v) for k, v in fields.items()}

        assert CONF_LOCAL_ADDRESS in field_map
        assert CONF_INTERPOLATION_FREQUENCY in field_map
        k_interp, v_interp = field_map[CONF_INTERPOLATION_FREQUENCY]
        assert k_interp.default() == DEFAULT_INTERPOLATION_FREQUENCY
        assert v_interp.config["min"] == MIN_INTERPOLATION_FREQUENCY
        assert v_interp.config["max"] == MAX_INTERPOLATION_FREQUENCY

        assert CONF_ADDITIONAL_DELAY in field_map
        k_delay, v_delay = field_map[CONF_ADDITIONAL_DELAY]
        assert k_delay.default() == DEFAULT_ADDITIONAL_DELAY
        assert v_delay.config["min"] == MIN_ADDITIONAL_DELAY
        assert v_delay.config["max"] == MAX_ADDITIONAL_DELAY

        assert CONF_MIN_DIM_DURATION in field_map
        k_min_dim, v_min_dim = field_map[CONF_MIN_DIM_DURATION]
        assert k_min_dim.default() == DEFAULT_MIN_DIM_DURATION
        assert v_min_dim.config["min"] == MIN_DIM_DURATION
        assert v_min_dim.config["max"] == MAX_DIM_DURATION

        assert CONF_MAX_DIM_DURATION in field_map
        k_max_dim, v_max_dim = field_map[CONF_MAX_DIM_DURATION]
        assert k_max_dim.default() == DEFAULT_MAX_DIM_DURATION
        assert v_max_dim.config["min"] == MIN_DIM_DURATION
        assert v_max_dim.config["max"] == MAX_DIM_DURATION

        assert CONF_SCAN_INTERVAL in field_map
        k_scan, v_scan = field_map[CONF_SCAN_INTERVAL]
        assert k_scan.default() == DEFAULT_SCAN_INTERVAL
        assert v_scan.config["min"] == 0
        assert v_scan.config["max"] == 720

        assert CONF_FORCE_UPDATE in field_map
        k_force, _ = field_map[CONF_FORCE_UPDATE]
        assert k_force.default() is False

    def test_get_options_schema_custom_data(self):
        custom = {
            CONF_LOCAL_ADDRESS: "10.0.0.1",
            CONF_INTERPOLATION_FREQUENCY: 10,
            CONF_ADDITIONAL_DELAY: 500,
            CONF_MIN_DIM_DURATION: 100,
            CONF_MAX_DIM_DURATION: 3000,
            CONF_SCAN_INTERVAL: 15,
            CONF_FORCE_UPDATE: True,
        }
        schema = _get_options_schema(custom)
        field_map = {k.schema: (k, v) for k, v in schema.schema.items()}
        assert field_map[CONF_LOCAL_ADDRESS][0].default() == "10.0.0.1"
        assert field_map[CONF_INTERPOLATION_FREQUENCY][0].default() == 10
        assert field_map[CONF_ADDITIONAL_DELAY][0].default() == 500
        assert field_map[CONF_MIN_DIM_DURATION][0].default() == 100
        assert field_map[CONF_MAX_DIM_DURATION][0].default() == 3000
        assert field_map[CONF_SCAN_INTERVAL][0].default() == 15
        assert field_map[CONF_FORCE_UPDATE][0].default() is True
