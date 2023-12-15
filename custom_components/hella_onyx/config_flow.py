"""Config flow for the ONYX integration."""
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
    FlowResult,
    CONN_CLASS_LOCAL_POLL,
)
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from onyx_client.client import create

from .const import (
    CONF_FINGERPRINT,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_INTERVAL,
    DOMAIN,
)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FINGERPRINT): cv.string,
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): cv.positive_int,
        vol.Required(
            CONF_MIN_DIM_DURATION, default=DEFAULT_MIN_DIM_DURATION
        ): cv.positive_int,
        vol.Required(
            CONF_MAX_DIM_DURATION, default=DEFAULT_MAX_DIM_DURATION
        ): cv.positive_int,
        vol.Required(CONF_FORCE_UPDATE, default=False): cv.boolean,
    }
)


class OnyxFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONYX."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        return await self.async_step_init(user_input)

    async def async_step_import(self, user_input=None):
        """Handle a flow initiated by import."""
        return await self.async_step_init(user_input, is_import=True)

    async def async_step_init(self, user_input, is_import=False):
        """Handle init step of a flow."""
        if user_input is not None:
            fingerprint = user_input[CONF_FINGERPRINT]
            token = user_input[CONF_ACCESS_TOKEN]
            scan_interval = user_input[CONF_SCAN_INTERVAL]
            min_dim_duration = user_input[CONF_MIN_DIM_DURATION]
            max_dim_duration = user_input[CONF_MAX_DIM_DURATION]
            force_update = user_input[CONF_FORCE_UPDATE]

            if await self._async_exists(fingerprint):
                return self.async_abort(reason="already_configured")

            if not await self._async_verify_conn(fingerprint, token):
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title="ONYX",
                data={
                    CONF_FINGERPRINT: fingerprint,
                    CONF_ACCESS_TOKEN: token,
                    CONF_SCAN_INTERVAL: scan_interval,
                    CONF_MIN_DIM_DURATION: min_dim_duration,
                    CONF_MAX_DIM_DURATION: max_dim_duration,
                    CONF_FORCE_UPDATE: force_update,
                },
            )

        errors = {}

        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def _async_exists(self, fingerprint):
        """Check if the endpoint exists already."""
        existing_fingerprints = [
            f"{entry.data.get(CONF_FINGERPRINT)}"
            for entry in self._async_current_entries()
        ]
        return fingerprint in existing_fingerprints

    async def _async_verify_conn(self, fingerprint, token):
        """Verify the connection credentials."""
        return await create(
            fingerprint=fingerprint,
            access_token=token,
            client_session=async_get_clientsession(self.hass, False),
        ).verify()


class OptionsFlowHandler(OptionsFlow):
    """Handle a option flow for ONYX."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MIN_DIM_DURATION,
                    default=self.config_entry.options.get(
                        CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
                    ),
                ): cv.positive_int,
                vol.Required(
                    CONF_MAX_DIM_DURATION,
                    default=self.config_entry.options.get(
                        CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
                    ),
                ): cv.positive_int,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_INTERVAL
                    ),
                ): cv.positive_int,
                vol.Required(
                    CONF_FORCE_UPDATE,
                    default=self.config_entry.options.get(CONF_FORCE_UPDATE, False),
                ): cv.boolean,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
