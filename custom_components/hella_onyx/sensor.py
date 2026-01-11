"""The ONYX sensors."""

import logging

from typing import Callable, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from onyx_client.enum.device_type import DeviceType
from onyx_client.device.weather import Weather

from custom_components.hella_onyx.api_connector import APIConnector

from . import ONYX_API, ONYX_TIMEZONE
from .const import DOMAIN
from .sensors.device_type import OnyxSensorDeviceType
from .sensors.weather import (
    OnyxSensorWeatherHumidity,
    OnyxSensorWeatherTemperature,
    OnyxSensorWeatherAirPressure,
    OnyxSensorWeatherWindPeak,
    OnyxSensorWeatherSunBrightnessPeak,
    OnyxSensorWeatherSunBrightnessSink,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the ONYX platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data[ONYX_API]
    timezone = data[ONYX_TIMEZONE]

    # all device type sensors
    sensors = [
        [
            OnyxSensorDeviceType(
                api, timezone, device.name, device.device_type, device_id
            ),
        ]
        # we only support shutters or weather stations
        for device_id, device in filter(
            lambda item: item[1].device_type is not None
            and (
                item[1].device_type.is_shutter()
                or item[1].device_type.is_light()
                or item[1].device_type == DeviceType.WEATHER
            ),
            api.devices.items(),
        )
    ]
    # all weather stations
    sensors = sensors + [
        _collect_weather_sensors(api, timezone, device, device_id)
        for device_id, device in filter(
            lambda item: item[1].device_type == DeviceType.WEATHER, api.devices.items()
        )
    ]
    sensors = [item for sublist in sensors for item in sublist]

    _LOGGER.info("adding %s hella_onyx sensor entities", len(sensors))
    async_add_entities(sensors, True)


def _collect_weather_sensors(
    api: APIConnector, timezone: str, device: Weather, device_id: str
):
    sensors = [
        OnyxSensorWeatherTemperature(
            api, timezone, device.name, device.device_type, device_id
        ),
        OnyxSensorWeatherWindPeak(
            api, timezone, device.name, device.device_type, device_id
        ),
        OnyxSensorWeatherSunBrightnessPeak(
            api, timezone, device.name, device.device_type, device_id
        ),
        OnyxSensorWeatherSunBrightnessSink(
            api, timezone, device.name, device.device_type, device_id
        ),
    ]

    if device.humidity is not None:
        sensors += (
            OnyxSensorWeatherHumidity(
                api, timezone, device.name, device.device_type, device_id
            ),
        )
    if device.air_pressure is not None:
        sensors += (
            OnyxSensorWeatherAirPressure(
                api, timezone, device.name, device.device_type, device_id
            ),
        )

    return sensors
