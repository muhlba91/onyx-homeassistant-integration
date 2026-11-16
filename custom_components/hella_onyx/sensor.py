"""The ONYX sensors."""

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import DiscoveryInfoType
from onyx_client.device.device import Device
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.api_connector import APIConnector

from . import OnyxConfigEntry
from .devices import is_supported
from .sensors.active_command import OnyxSensorActiveCommand
from .sensors.device_type import OnyxSensorDeviceType, OnyxSensorUnknownDeviceType
from .sensors.system_state import OnyxSensorSystemState
from .sensors.weather import (
    OnyxSensorWeatherAirPressure,
    OnyxSensorWeatherHumidity,
    OnyxSensorWeatherSunBrightness,
    OnyxSensorWeatherSunBrightnessPeak,
    OnyxSensorWeatherSunBrightnessSink,
    OnyxSensorWeatherTemperature,
    OnyxSensorWeatherWindPeak,
    OnyxSensorWeatherWindSpeed,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnyxConfigEntry,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the ONYX platform."""
    api = entry.runtime_data.api
    timezone = entry.runtime_data.timezone

    sensors = []
    for device_id, device in api.devices.items():
        device_type = device.device_type
        args = (api, timezone, device.name, device_type, device_id)
        if device_type == DeviceType.UNKNOWN:
            _LOGGER.info(
                "device %s has the unsupported type %s", device_id, device.raw_type
            )
            sensors.append(OnyxSensorUnknownDeviceType(*args))
            continue
        if not is_supported(device_type):
            continue
        sensors.append(OnyxSensorDeviceType(*args))
        # weather stations, tags and shutters (pergola units measure temperature
        # and humidity) report (a subset of) weather values
        if (
            device_type == DeviceType.WEATHER
            or device_type.is_tag()
            or device_type.is_shutter()
        ):
            sensors.extend(_collect_weather_sensors(api, timezone, device, device_id))
        # diagnostic sensors of controllable devices
        if device_type.is_shutter() and getattr(device, "system_state", None):
            sensors.append(OnyxSensorSystemState(*args))
        if device_type.is_shutter() or device_type.is_light():
            sensors.append(OnyxSensorActiveCommand(*args))

    _LOGGER.info("adding %s hella_onyx sensor entities", len(sensors))
    async_add_entities(sensors)


def _collect_weather_sensors(
    api: APIConnector, timezone: str, device: Device, device_id: str
):
    sensors = []

    if getattr(device, "temperature", None) is not None:
        sensors.append(
            OnyxSensorWeatherTemperature(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "humidity", None) is not None:
        sensors.append(
            OnyxSensorWeatherHumidity(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "air_pressure", None) is not None:
        sensors.append(
            OnyxSensorWeatherAirPressure(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "wind_peak", None) is not None:
        sensors.append(
            OnyxSensorWeatherWindPeak(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "wind_speed", None) is not None:
        sensors.append(
            OnyxSensorWeatherWindSpeed(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "sun_brightness_peak", None) is not None:
        sensors.append(
            OnyxSensorWeatherSunBrightnessPeak(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "sun_brightness_sink", None) is not None:
        sensors.append(
            OnyxSensorWeatherSunBrightnessSink(
                api, timezone, device.name, device.device_type, device_id
            )
        )
    if getattr(device, "sun_brightness", None) is not None:
        sensors.append(
            OnyxSensorWeatherSunBrightness(
                api, timezone, device.name, device.device_type, device_id
            )
        )

    return sensors
