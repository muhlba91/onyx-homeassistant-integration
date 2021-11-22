"""The ONYX.CENTER integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
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
    ONYX_THREAD,
    ONYX_TIMEZONE,
)
from .event_thread import EventThread

_LOGGER = logging.getLogger(__name__)

ONYX_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_FINGERPRINT): cv.string,
            vol.Required(CONF_ACCESS_TOKEN): cv.string,
            vol.Required(CONF_SCAN_INTERVAL): cv.positive_int,
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
    force_update = entry.data.get(CONF_FORCE_UPDATE, False)

    _LOGGER.debug("setting up %s integration with fingerprint %s", DOMAIN, fingerprint)
    if force_update:
        _LOGGER.warning(
            "Disabling partial updates. "
            "This may lead to a higher amount of API calls to Hella, "
            "and performance impacts. It is advised to not enable this option."
        )

    onyx_api = APIConnector(hass, fingerprint, token)
    await onyx_api.update()
    onyx_timezone = await onyx_api.get_timezone()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ONYX",
        update_method=onyx_api.update,
        update_interval=timedelta(minutes=scan_interval),
        request_refresh_debouncer=Debouncer(hass, _LOGGER, cooldown=0, immediate=True),
    )

    thread = EventThread(onyx_api, coordinator, force_update)
    hass.data[DOMAIN][entry.entry_id] = {
        ONYX_API: onyx_api,
        ONYX_TIMEZONE: onyx_timezone,
        ONYX_COORDINATOR: coordinator,
        ONYX_THREAD: thread,
    }
    thread.start()

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
