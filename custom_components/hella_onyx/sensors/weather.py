"""The ONYX weather sensors."""
from typing import Optional

from custom_components.hella_onyx.sensors.onyx_entity import OnyxEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    LIGHT_LUX,
    PERCENTAGE,
)


class OnyxSensorWeatherHumidity(OnyxEntity, SensorEntity):
    """ONYX Weather Humidity Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Humidity"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Humidity"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:water-percent"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.HUMIDITY

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return PERCENTAGE

    @property
    def native_value(self) -> int:
        """Return the current value."""
        return self._device.humidity.value


class OnyxSensorWeatherTemperature(OnyxEntity, SensorEntity):
    """ONYX Weather Temperature Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Temperature"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Temperature"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:thermometer"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._device.temperature.value / 10


class OnyxSensorWeatherAirPressure(OnyxEntity, SensorEntity):
    """ONYX Weather Air Pressure Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Air Pressure"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/AirPressure"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:gauge"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.ATMOSPHERIC_PRESSURE

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return UnitOfPressure.HPA

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._device.air_pressure.value / 100


class OnyxSensorWeatherWindPeak(OnyxEntity, SensorEntity):
    """ONYX Weather Wind Peak Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Wind Peak"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/WindPeak"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:weather-windy"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.WIND_SPEED

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return UnitOfSpeed.METERS_PER_SECOND

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._device.wind_peak.value / 1000


class OnyxSensorWeatherSunBrightnessPeak(OnyxEntity, SensorEntity):
    """ONYX Weather Sun Brightness Peak Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Sun Brightness Peak"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/SunBrightnessPeak"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:weather-sunset-up"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.ILLUMINANCE

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return LIGHT_LUX

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._device.sun_brightness_peak.value


class OnyxSensorWeatherSunBrightnessSink(OnyxEntity, SensorEntity):
    """ONYX Weather Sun Brightness Sink Sensor."""

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return f"{self._name} Sun Brightness Sink"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._uuid}/SunBrightnessSink"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:weather-sunset-down"

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component device class."""
        return SensorDeviceClass.ILLUMINANCE

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the native unit of this measurement."""
        return LIGHT_LUX

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._device.sun_brightness_sink.value
