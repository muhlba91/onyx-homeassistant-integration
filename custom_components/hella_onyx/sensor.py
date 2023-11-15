"""The ONYX sensors."""
import logging
from typing import Callable, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType

from onyx_client.enum.device_type import DeviceType

from . import ONYX_API, ONYX_COORDINATOR, ONYX_TIMEZONE
from .const import DOMAIN
from custom_components.hella_onyx.sensors.device_type import OnyxSensorDeviceType
from custom_components.hella_onyx.sensors.weather import (
    OnyxSensorWeatherHumidity,
    OnyxSensorWeatherTemperature,
    OnyxSensorWeatherAirPressure,
    OnyxSensorWeatherWindPeak,
    OnyxSensorWeatherSunBrightnessPeak,
    OnyxSensorWeatherSunBrightnessSink,
)

_LOGGER = logging.getLogger(__name__)


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
    coordinator = data[ONYX_COORDINATOR]

    # all device type sensors
    sensors = [
        [
            OnyxSensorDeviceType(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
        ]
        # we only support shutters or weather stations
        for device_id, device in filter(
            lambda item: item[1].device_type.is_shutter()
            or item[1].device_type == DeviceType.WEATHER,
            api.devices.items(),
        )
    ]
    # all weather stations
    sensors = sensors + [
        [
            OnyxSensorWeatherHumidity(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorWeatherTemperature(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorWeatherAirPressure(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorWeatherWindPeak(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorWeatherSunBrightnessPeak(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
            OnyxSensorWeatherSunBrightnessSink(
                api, timezone, coordinator, device.name, device.device_type, device_id
            ),
        ]
        for device_id, device in filter(
            lambda item: item[1].device_type == DeviceType.WEATHER, api.devices.items()
        )
    ]
    sensors = [item for sublist in sensors for item in sublist]

    _LOGGER.info("adding %s hella_onyx sensor entities", len(sensors))
    async_add_entities(sensors, True)
