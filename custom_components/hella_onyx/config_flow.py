"""Config flow for the ONYX integration."""

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_PUSH,
    ConfigEntry,
    ConfigFlow,
    FlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CODE,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from onyx_client.authorizer import authorize
from onyx_client.client import create
from onyx_client.enum.verify_result import VerifyResult

from .configuration import normalize_local_address
from .const import (
    CONF_ADDITIONAL_DELAY,
    CONF_CLOSED_TOLERANCE,
    CONF_FINGERPRINT,
    CONF_INTERPOLATION_FREQUENCY,
    CONF_LOCAL_ADDRESS,
    CONF_MAX_DIM_DURATION,
    CONF_MIN_DIM_DURATION,
    CONF_MOVING_TIMEOUT,
    DEFAULT_ADDITIONAL_DELAY,
    DEFAULT_CLOSED_TOLERANCE,
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MOVING_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_ADDITIONAL_DELAY,
    MAX_CLOSED_TOLERANCE,
    MAX_DIM_DURATION,
    MAX_INTERPOLATION_FREQUENCY,
    MAX_MOVING_TIMEOUT,
    MIN_ADDITIONAL_DELAY,
    MIN_CLOSED_TOLERANCE,
    MIN_DIM_DURATION,
    MIN_INTERPOLATION_FREQUENCY,
    MIN_MOVING_TIMEOUT,
)

VERIFY_ERRORS = {
    VerifyResult.UNREACHABLE: "cannot_connect",
    VerifyResult.UNAUTHORIZED: "invalid_auth",
    VerifyResult.VERSION_UNSUPPORTED: "api_version_unsupported",
}


class OnyxFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ONYX."""

    VERSION = 3
    MINOR_VERSION = 3
    CONNECTION_CLASS = CONN_CLASS_CLOUD_PUSH

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

            fingerprint = user_input.get(CONF_FINGERPRINT)
            token = user_input.get(CONF_ACCESS_TOKEN)
            code = user_input.get(CONF_CODE)
            local_address = normalize_local_address(user_input.get(CONF_LOCAL_ADDRESS))

            options.update(self._options)
            _store_local_address(options, local_address)
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

            if not errors:
                result = await self._async_verify_conn(
                    fingerprint, token, local_address
                )
                if result != VerifyResult.OK:
                    errors["base"] = VERIFY_ERRORS[result]

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
            # pragma: no mutate start
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
                        description={
                            "suggested_value": options.get(CONF_LOCAL_ADDRESS)
                        },
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                }
            ),
            # pragma: no mutate end
            errors=errors,
        )

    async def async_step_options(self, user_input=None):
        """Handle an options flow initiated by the user."""
        errors = {}

        if user_input is not None:
            local_address = normalize_local_address(user_input.get(CONF_LOCAL_ADDRESS))
            scan_interval = user_input[CONF_SCAN_INTERVAL]
            additional_delay = max(
                MIN_ADDITIONAL_DELAY, user_input[CONF_ADDITIONAL_DELAY]
            )
            interpolation_frequency = max(
                MIN_INTERPOLATION_FREQUENCY, user_input[CONF_INTERPOLATION_FREQUENCY]
            )
            closed_tolerance = min(
                MAX_CLOSED_TOLERANCE,
                max(MIN_CLOSED_TOLERANCE, user_input[CONF_CLOSED_TOLERANCE]),
            )
            moving_timeout = min(
                MAX_MOVING_TIMEOUT,
                max(MIN_MOVING_TIMEOUT, user_input[CONF_MOVING_TIMEOUT]),
            )
            min_dim_duration = max(MIN_DIM_DURATION, user_input[CONF_MIN_DIM_DURATION])
            max_dim_duration = min(MAX_DIM_DURATION, user_input[CONF_MAX_DIM_DURATION])

            options = {
                CONF_SCAN_INTERVAL: scan_interval,
                CONF_INTERPOLATION_FREQUENCY: interpolation_frequency,
                CONF_ADDITIONAL_DELAY: additional_delay,
                CONF_CLOSED_TOLERANCE: closed_tolerance,
                CONF_MOVING_TIMEOUT: moving_timeout,
                CONF_MIN_DIM_DURATION: min_dim_duration,
                CONF_MAX_DIM_DURATION: max_dim_duration,
            }
            _store_local_address(options, local_address)

            if not errors:
                # the address is not a default, so a cleared one is not submitted
                self._options.pop(CONF_LOCAL_ADDRESS, None)
                self._options.update(options)

                return self.async_create_entry(
                    title=self._data[CONF_FINGERPRINT],
                    data=self._data,
                    options=options,
                )

        return self.async_show_form(
            step_id="options",
            data_schema=_get_options_schema(data=self._options),
            errors=errors,
        )

    async def async_step_reauth(self, data) -> FlowResult:
        """Handle initiation of re-authentication."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        # the entry data holds no local address and all options must survive: seed
        # both from the entry, so the credentials are verified against the stored
        # address and the entry stays on the local API. The form still lets the
        # user change or clear the address.
        self._options = dict(self._entry.options)
        user_input = dict(data)
        stored_address = self._options.get(CONF_LOCAL_ADDRESS)
        if stored_address:
            user_input.setdefault(CONF_LOCAL_ADDRESS, stored_address)
        return await self.async_step_user(user_input)

    async def _async_verify_conn(
        self, fingerprint, token, local_address
    ) -> VerifyResult:
        """Verify the connection credentials."""
        return await create(
            fingerprint=fingerprint,
            access_token=token,
            client_session=async_get_clientsession(self.hass, False),
            local_address=local_address,
        ).verify()


def _store_local_address(options: dict, local_address: str | None) -> None:
    """Store the local address, or remove it for the cloud API; never store None."""
    if local_address:
        options[CONF_LOCAL_ADDRESS] = local_address
    else:
        options.pop(CONF_LOCAL_ADDRESS, None)


# pragma: no mutate start
class OnyxOptionsFlowHandler(OptionsFlow):
    """Handle a option flow for ONYX."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            data = dict(user_input)
            # the frontend omits a cleared field; the options replace the stored
            # ones, so an omitted or empty address selects the cloud API
            _store_local_address(
                data, normalize_local_address(data.get(CONF_LOCAL_ADDRESS))
            )
            return self.async_create_entry(title=self.config_entry.title, data=data)

        if user_input is None:
            user_input = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(data=self.config_entry.options),
        )


# pragma: no mutate end


# pragma: no mutate start
def _get_options_schema(data: dict | None = None):
    data = data if data is not None else {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_LOCAL_ADDRESS,
                description={"suggested_value": data.get(CONF_LOCAL_ADDRESS)},
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
                CONF_CLOSED_TOLERANCE,
                default=data.get(CONF_CLOSED_TOLERANCE, DEFAULT_CLOSED_TOLERANCE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_CLOSED_TOLERANCE,
                    max=MAX_CLOSED_TOLERANCE,
                )
            ),
            vol.Optional(
                CONF_MOVING_TIMEOUT,
                default=data.get(CONF_MOVING_TIMEOUT, DEFAULT_MOVING_TIMEOUT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_MOVING_TIMEOUT,
                    max=MAX_MOVING_TIMEOUT,
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
        }
    )


# pragma: no mutate end
