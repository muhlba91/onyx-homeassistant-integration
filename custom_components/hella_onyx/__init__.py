"""The ONYX.CENTER integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
    Platform,
)
from homeassistant.core import HomeAssistant

from .api_connector import APIConnector
from .configuration import Configuration
from .const import (
    CONF_FINGERPRINT,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    CONF_ADDITIONAL_DELAY,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_ADDITIONAL_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ONYX_API,
    ONYX_CONFIG,
    ONYX_TIMEZONE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ONYX from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    fingerprint = entry.data[CONF_FINGERPRINT]
    token = entry.data[CONF_ACCESS_TOKEN]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    additional_delay = entry.options.get(
        CONF_ADDITIONAL_DELAY, DEFAULT_ADDITIONAL_DELAY
    )
    min_dim_duration = entry.options.get(
        CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
    )
    max_dim_duration = entry.options.get(
        CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
    )
    force_update = entry.options.get(CONF_FORCE_UPDATE, False)

    _LOGGER.debug("setting up %s integration with fingerprint %s", DOMAIN, fingerprint)
    if force_update:
        _LOGGER.warning(
            "Disabling partial updates. "
            "This may lead to a higher amount of API calls to Hella, "
            "and performance impacts. It is advised to not enable this option."
        )

    onyx_config = Configuration(
        scan_interval,
        min_dim_duration,
        max_dim_duration,
        additional_delay,
        force_update,
        fingerprint,
        token,
    )
    _LOGGER.info("using config: %s", onyx_config)
    onyx_api = APIConnector(hass, onyx_config)
    await onyx_api.async_config_entry_first_refresh()
    onyx_timezone = await onyx_api.get_timezone()

    hass.data[DOMAIN][entry.entry_id] = {
        ONYX_API: onyx_api,
        ONYX_CONFIG: onyx_config,
        ONYX_TIMEZONE: onyx_timezone,
    }
    hass.async_create_background_task(onyx_api.events(force_update), name=DOMAIN)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


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
            CONF_FORCE_UPDATE: old_data.get(CONF_FORCE_UPDATE, False),
        }
        config_entry.data = new_data
        config_entry.options = new_options

        config_entry.version = 2
        config_entry.minor_version = 1

    if config_entry.version == 2 and config_entry.minor_version == 1:
        old_options = {**config_entry.options}

        new_options = {
            CONF_SCAN_INTERVAL: old_options.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            ),
            CONF_MIN_DIM_DURATION: old_options.get(
                CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION
            ),
            CONF_MAX_DIM_DURATION: old_options.get(
                CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION
            ),
            CONF_ADDITIONAL_DELAY: old_options.get(
                CONF_ADDITIONAL_DELAY, DEFAULT_ADDITIONAL_DELAY
            ),
            CONF_FORCE_UPDATE: old_options.get(CONF_FORCE_UPDATE, False),
        }
        config_entry.options = new_options

        config_entry.version = 2
        config_entry.minor_version = 2

    _LOGGER.info(
        "migration to version %d.%d successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True
