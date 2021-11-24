"""Config flow for the ONYX integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from onyx_client.client import create

from .const import CONF_FINGERPRINT, DEFAULT_INTERVAL, DOMAIN

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FINGERPRINT): cv.string,
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): cv.positive_int,
        vol.Required(CONF_FORCE_UPDATE, default=False): cv.boolean,
    }
)


class OnyxFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONYX."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

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
                    CONF_FORCE_UPDATE: force_update,
                },
            )

        errors = {}

        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_SCHEMA,
            errors=errors,
        )

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
