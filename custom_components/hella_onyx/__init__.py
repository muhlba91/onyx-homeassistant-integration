"""The ONYX.CENTER integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api_connector import APIConnector
from .const import (
    CONF_FINGERPRINT,
    DOMAIN,
    ONYX_API,
    ONYX_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

ONYX_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_FINGERPRINT): cv.string,
            vol.Required(CONF_ACCESS_TOKEN): cv.string,
            vol.Required(CONF_SCAN_INTERVAL): cv.positive_int,
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
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setting up %s integration with fingerprint %s", DOMAIN, fingerprint)

    onyx_api = APIConnector(hass, fingerprint, token)
    await onyx_api.update()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ONYX",
        update_method=onyx_api.update,
        update_interval=timedelta(minutes=scan_interval),
        request_refresh_debouncer=Debouncer(hass, _LOGGER, cooldown=0, immediate=True),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        ONYX_API: onyx_api,
        ONYX_COORDINATOR: coordinator,
    }

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
