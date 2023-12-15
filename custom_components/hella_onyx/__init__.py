"""The ONYX.CENTER integration."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .api_connector import APIConnector
from .configuration import Configuration
from .const import (
    CONF_FINGERPRINT,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_INTERVAL,
    DOMAIN,
    ONYX_API,
    ONYX_CONFIG,
    ONYX_TIMEZONE,
)

_LOGGER = logging.getLogger(__name__)

ONYX_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_FINGERPRINT): cv.string,
            vol.Required(CONF_ACCESS_TOKEN): cv.string,
            vol.Required(CONF_SCAN_INTERVAL): cv.positive_int,
            vol.Required(CONF_MIN_DIM_DURATION): cv.positive_int,
            vol.Required(CONF_MAX_DIM_DURATION): cv.positive_int,
            vol.Required(CONF_FORCE_UPDATE, default=False): cv.boolean,
        },
    )
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [ONYX_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [
    "cover",
    "sensor",
    "light",
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up ONYX component via configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ONYX from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    fingerprint = entry.data[CONF_FINGERPRINT]
    token = entry.data[CONF_ACCESS_TOKEN]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_INTERVAL)
    min_dim_duration = entry.data.get(CONF_MIN_DIM_DURATION, DEFAULT_MIN_DIM_DURATION)
    max_dim_duration = entry.data.get(CONF_MAX_DIM_DURATION, DEFAULT_MAX_DIM_DURATION)
    force_update = entry.data.get(CONF_FORCE_UPDATE, False)

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
        force_update,
        fingerprint,
        token,
    )
    _LOGGER.debug("using config: %s", onyx_config)
    onyx_api = APIConnector(hass, onyx_config)
    await onyx_api.async_config_entry_first_refresh()
    onyx_timezone = await onyx_api.get_timezone()

    hass.data[DOMAIN][entry.entry_id] = {
        ONYX_API: onyx_api,
        ONYX_CONFIG: onyx_config,
        ONYX_TIMEZONE: onyx_timezone,
    }
    hass.async_create_background_task(onyx_api.events(force_update), name=DOMAIN)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform),
        )

    return True


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
