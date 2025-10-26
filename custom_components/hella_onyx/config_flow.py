"""Config flow for the ONYX integration."""

import voluptuous as vol

from homeassistant.helpers import selector
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
    CONF_CODE,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from onyx_client.client import create
from onyx_client.authorizer import authorize

from .const import (
    CONF_FINGERPRINT,
    CONF_LOCAL_ADDRESS,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    CONF_ADDITIONAL_DELAY,
    CONF_INTERPOLATION_FREQUENCY,
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_ADDITIONAL_DELAY,
    MAX_INTERPOLATION_FREQUENCY,
    MIN_DIM_DURATION,
    MAX_DIM_DURATION,
    MIN_ADDITIONAL_DELAY,
    MAX_ADDITIONAL_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_INTERPOLATION_FREQUENCY,
)


class OnyxFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONYX."""

    VERSION = 3
    MINOR_VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        self._data = {}
        self._options = {}
        self._entry: ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "OnyxOptionsFlowHandler":
        """Get the options flow for this handler."""
        return OnyxOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}
        data = {}
        options = {}

        if user_input is not None:
            data.update(user_input)

            fingerprint = user_input.get(CONF_FINGERPRINT, None)
            token = user_input.get(CONF_ACCESS_TOKEN, None)
            code = user_input.get(CONF_CODE, None)
            local_address = user_input.get(CONF_LOCAL_ADDRESS, None)

            options.update(self._options)
            options[CONF_LOCAL_ADDRESS] = local_address
            data.pop(CONF_LOCAL_ADDRESS, None)

            if code is not None:
                config = await authorize(
                    code,
                    client_session=async_get_clientsession(self.hass, False),
                    local_address=local_address,
                )
                if config is not None:
                    fingerprint = config.fingerprint
                    token = config.access_token
                    data[CONF_FINGERPRINT] = fingerprint
                    data[CONF_ACCESS_TOKEN] = token
                    data.pop(CONF_CODE)
                else:
                    errors[CONF_CODE] = "invalid_code"

            if not errors and not await self._async_verify_conn(
                fingerprint, token, local_address
            ):
                errors[CONF_ACCESS_TOKEN] = "invalid_connection_data"

            if not errors:
                if self._entry:
                    self.hass.config_entries.async_update_entry(
                        self._entry, data=data, options=options
                    )
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(self._entry.entry_id)
                    )
                    return self.async_abort(reason="reauth_successful")

                self._async_abort_entries_match({CONF_FINGERPRINT: fingerprint})

                self._data.update(data)
                self._options.update(options)
                return await self.async_step_options()

        if self._entry:
            data.update(self._entry.data)
            options.update(self._entry.options)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CODE): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                    vol.Optional(
                        CONF_FINGERPRINT,
                        default=data.get(CONF_FINGERPRINT, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Optional(
                        CONF_ACCESS_TOKEN,
                        default=data.get(CONF_ACCESS_TOKEN, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                    vol.Optional(
                        CONF_LOCAL_ADDRESS,
                        default=data.get(CONF_LOCAL_ADDRESS, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_options(self, user_input=None):
        """Handle an options flow initiated by the user."""
        errors = {}
        options = {}

        if user_input is not None:
            local_address = user_input.get(CONF_LOCAL_ADDRESS, None)
            scan_interval = user_input[CONF_SCAN_INTERVAL]
            additional_delay = max(
                MIN_ADDITIONAL_DELAY, user_input[CONF_ADDITIONAL_DELAY]
            )
            interpolation_frequency = max(
                MIN_INTERPOLATION_FREQUENCY, user_input[CONF_INTERPOLATION_FREQUENCY]
            )
            min_dim_duration = max(MIN_DIM_DURATION, user_input[CONF_MIN_DIM_DURATION])
            max_dim_duration = min(MAX_DIM_DURATION, user_input[CONF_MAX_DIM_DURATION])
            force_update = user_input[CONF_FORCE_UPDATE]

            options = {
                CONF_LOCAL_ADDRESS: local_address,
                CONF_SCAN_INTERVAL: scan_interval,
                CONF_INTERPOLATION_FREQUENCY: interpolation_frequency,
                CONF_ADDITIONAL_DELAY: additional_delay,
                CONF_MIN_DIM_DURATION: min_dim_duration,
                CONF_MAX_DIM_DURATION: max_dim_duration,
                CONF_FORCE_UPDATE: force_update,
            }

            if not errors:
                self._options.update(options)

                return self.async_create_entry(
                    title=self._data[CONF_FINGERPRINT],
                    data=self._data,
                    options=options,
                )

        return self.async_show_form(
            step_id="options",
            data_schema=_get_options_schema(
                data=user_input if user_input else self._options
            ),
            errors=errors,
        )

    async def async_step_reauth(self, data) -> FlowResult:
        """Handle initiation of re-authentication."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_user(data)

    async def _async_verify_conn(self, fingerprint, token, local_address) -> bool:
        """Verify the connection credentials."""
        return await create(
            fingerprint=fingerprint,
            access_token=token,
            client_session=async_get_clientsession(self.hass, False),
            local_address=local_address,
        ).verify()


class OnyxOptionsFlowHandler(OptionsFlow):
    """Handle a option flow for ONYX."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        if user_input is None:
            user_input = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(data=self.config_entry.options),
        )


def _get_options_schema(data: dict | None = None):
    data = data if data is not None else {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_LOCAL_ADDRESS,
                default=data.get(CONF_LOCAL_ADDRESS, vol.UNDEFINED),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_INTERPOLATION_FREQUENCY,
                default=data.get(
                    CONF_INTERPOLATION_FREQUENCY, DEFAULT_INTERPOLATION_FREQUENCY
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_INTERPOLATION_FREQUENCY,
                    max=MAX_INTERPOLATION_FREQUENCY,
                )
            ),
            vol.Optional(
                CONF_ADDITIONAL_DELAY,
                default=data.get(CONF_ADDITIONAL_DELAY, DEFAULT_ADDITIONAL_DELAY),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_ADDITIONAL_DELAY,
                    max=MAX_ADDITIONAL_DELAY,
                )
            ),
            vol.Optional(
                CONF_MIN_DIM_DURATION,
                default=data.get(CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_DIM_DURATION,
                    max=MAX_DIM_DURATION,
                )
            ),
            vol.Optional(
                CONF_MAX_DIM_DURATION,
                default=data.get(CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_DIM_DURATION,
                    max=MAX_DIM_DURATION,
                )
            ),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=720,
                )
            ),
            vol.Optional(
                CONF_FORCE_UPDATE,
                default=data.get(CONF_FORCE_UPDATE, False),
            ): selector.BooleanSelector(),
        }
    )
