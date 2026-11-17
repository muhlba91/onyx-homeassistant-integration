"""The ONYX.CENTER integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_FORCE_UPDATE,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from onyx_client.utils.sanitize import protect

from .api_connector import APIConnector
from .configuration import Configuration, normalize_local_address
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
)
from .models import OnyxData

_LOGGER = protect(logging.getLogger(__name__))

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]

type OnyxConfigEntry = ConfigEntry[OnyxData]


async def async_setup_entry(hass: HomeAssistant, entry: OnyxConfigEntry) -> bool:
    """Set up ONYX from a config entry."""
    fingerprint = entry.data[CONF_FINGERPRINT]
    token = entry.data[CONF_ACCESS_TOKEN]
    local_address = normalize_local_address(entry.options.get(CONF_LOCAL_ADDRESS))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    interpolation_frequency = entry.options.get(
        CONF_INTERPOLATION_FREQUENCY, DEFAULT_INTERPOLATION_FREQUENCY
    )
    additional_delay = entry.options.get(
        CONF_ADDITIONAL_DELAY, DEFAULT_ADDITIONAL_DELAY
    )
    closed_tolerance = entry.options.get(
        CONF_CLOSED_TOLERANCE, DEFAULT_CLOSED_TOLERANCE
    )
    moving_timeout = entry.options.get(CONF_MOVING_TIMEOUT, DEFAULT_MOVING_TIMEOUT)
    min_dim_duration = entry.options.get(
        CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
    )
    max_dim_duration = entry.options.get(
        CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
    )

    _LOGGER.debug("setting up %s integration", DOMAIN)

    onyx_config = Configuration(
        scan_interval,
        min_dim_duration,
        max_dim_duration,
        additional_delay,
        interpolation_frequency,
        closed_tolerance,
        moving_timeout,
        fingerprint,
        token,
        local_address,
    )
    # the fingerprint is deliberately logged: it is no credential, and the client
    # identifies the ONYX.CENTER by it in its own logs; the token is not part of
    # Configuration.__str__
    _LOGGER.info(
        "using the %s API: %s",
        "local" if onyx_config.is_local else "cloud",
        onyx_config,
    )
    onyx_api = APIConnector(hass, onyx_config, entry)
    await onyx_api.async_config_entry_first_refresh()
    onyx_timezone = await onyx_api.get_timezone()

    entry.runtime_data = OnyxData(
        api=onyx_api,
        config=onyx_config,
        timezone=onyx_timezone,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: OnyxConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: OnyxConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "migrating from version %d.%d", config_entry.version, config_entry.minor_version
    )

    if config_entry.version == 1:
        old_data = {**config_entry.data}

        new_data = {
            CONF_FINGERPRINT: old_data.get(CONF_FINGERPRINT),
            CONF_ACCESS_TOKEN: old_data.get(CONF_ACCESS_TOKEN),
        }
        new_options = {
            CONF_SCAN_INTERVAL: old_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_MIN_DIM_DURATION: old_data.get(
                CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
            ),
            CONF_MAX_DIM_DURATION: old_data.get(
                CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
            ),
        }
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, options=new_options, version=2, minor_version=1
        )

    if config_entry.version == 2:
        old_data = {**config_entry.data}

        new_data = {
            CONF_FINGERPRINT: old_data.get(CONF_FINGERPRINT),
            CONF_ACCESS_TOKEN: old_data.get(CONF_ACCESS_TOKEN),
        }
        new_options = {
            CONF_SCAN_INTERVAL: old_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_INTERPOLATION_FREQUENCY: old_data.get(
                CONF_INTERPOLATION_FREQUENCY, DEFAULT_INTERPOLATION_FREQUENCY
            ),
            CONF_MIN_DIM_DURATION: old_data.get(
                CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
            ),
            CONF_MAX_DIM_DURATION: old_data.get(
                CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
            ),
        }
        if old_data.get(CONF_LOCAL_ADDRESS):
            new_options[CONF_LOCAL_ADDRESS] = old_data[CONF_LOCAL_ADDRESS]
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, options=new_options, version=3, minor_version=1
        )

    if config_entry.version == 3 and config_entry.minor_version < 2:
        new_options = {
            **config_entry.options,
            CONF_CLOSED_TOLERANCE: config_entry.options.get(
                CONF_CLOSED_TOLERANCE, DEFAULT_CLOSED_TOLERANCE
            ),
            CONF_MOVING_TIMEOUT: config_entry.options.get(
                CONF_MOVING_TIMEOUT, DEFAULT_MOVING_TIMEOUT
            ),
        }
        hass.config_entries.async_update_entry(
            config_entry, options=new_options, minor_version=2
        )

    if config_entry.version == 3 and config_entry.minor_version < 3:
        # force_update was removed with the event stream (API v6)
        new_options = {
            key: value
            for key, value in config_entry.options.items()
            if key != CONF_FORCE_UPDATE
        }
        hass.config_entries.async_update_entry(
            config_entry, options=new_options, minor_version=3
        )

    _LOGGER.info(
        "migration to version %d.%d successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True
