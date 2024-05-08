"""Test for the ONYX Weather Sensors."""

import pytest

from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    LIGHT_LUX,
    PERCENTAGE,
)

from onyx_client.data.device_mode import DeviceMode
from onyx_client.data.numeric_value import NumericValue
from onyx_client.device.weather import Weather
from onyx_client.enum.action import Action
from onyx_client.enum.device_type import DeviceType

from custom_components.hella_onyx.sensors.weather import (
    OnyxSensorWeatherHumidity,
    OnyxSensorWeatherTemperature,
    OnyxSensorWeatherAirPressure,
    OnyxSensorWeatherWindPeak,
    OnyxSensorWeatherSunBrightnessPeak,
    OnyxSensorWeatherSunBrightnessSink,
)


class TestOnyxSensorWeatherHumidity:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(0, 0, 1, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(3, 3, 4, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(5, 5, 6, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherHumidity(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:water-percent"

    def test_name(self, entity):
        assert entity.name == "name Humidity"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Humidity"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.HUMIDITY

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 0

    def test_unit_of_measurement(self, entity):
        assert entity.unit_of_measurement == PERCENTAGE

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == 4
        assert api.device.called


class TestOnyxSensorWeatherTemperature:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(0, 0, 1, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(3, 3, 4, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(50, 50, 60, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherTemperature(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:thermometer"

    def test_name(self, entity):
        assert entity.name == "name Temperature"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/Temperature"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.TEMPERATURE

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 1

    def test_unit_of_measurement(self, entity, hass):
        hass.config.units.temperature_unit = UnitOfTemperature.CELSIUS
        assert entity.unit_of_measurement == UnitOfTemperature.CELSIUS
        assert entity.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_state(self, api, entity, device, hass):
        hass.config.units.temperature_unit = UnitOfTemperature.CELSIUS
        api.device.return_value = device
        assert entity.state == 5.0
        assert api.device.called


class TestOnyxSensorWeatherAirPressure:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(0, 0, 1, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(300, 300, 400, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(50, 50, 60, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherAirPressure(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:gauge"

    def test_name(self, entity):
        assert entity.name == "name Air Pressure"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/AirPressure"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.ATMOSPHERIC_PRESSURE

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 1

    def test_unit_of_measurement(self, entity):
        assert entity.unit_of_measurement == UnitOfPressure.HPA

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == 3.0
        assert api.device.called


class TestOnyxSensorWeatherWindPeak:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(6000, 6000, 7000, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(300, 300, 400, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(50, 50, 60, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherWindPeak(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:weather-windy"

    def test_name(self, entity):
        assert entity.name == "name Wind Peak"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/WindPeak"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.WIND_SPEED

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 1

    def test_unit_of_measurement(self, entity):
        assert entity.unit_of_measurement == UnitOfSpeed.METERS_PER_SECOND

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == 6.0
        assert api.device.called


class TestOnyxSensorWeatherSunBrightnessPeak:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(6000, 6000, 7000, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(300, 300, 400, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(50, 50, 60, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherSunBrightnessPeak(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:weather-sunset-up"

    def test_name(self, entity):
        assert entity.name == "name Sun Brightness Peak"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/SunBrightnessPeak"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.ILLUMINANCE

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 0

    def test_unit_of_measurement(self, entity):
        assert entity.unit_of_measurement == LIGHT_LUX

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == 1
        assert api.device.called


class TestOnyxSensorWeatherSunBrightnessSink:
    @pytest.fixture
    def api(self):
        yield MagicMock()

    @pytest.fixture
    def hass(self):
        yield MagicMock()

    @pytest.fixture
    def device(self):
        yield Weather(
            "id",
            "name",
            DeviceType.WEATHER,
            DeviceMode(DeviceType.WEATHER),
            list(Action),
            NumericValue(6000, 6000, 7000, True),  # wind peak
            NumericValue(1, 1, 2, True),  # sun brightness peak
            NumericValue(2, 2, 3, True),  # sun brightness sink
            NumericValue(300, 300, 400, True),  # air pressure
            NumericValue(4, 4, 5, True),  # humidity
            NumericValue(50, 50, 60, True),  # temperature
        )

    @pytest.fixture
    def entity(self, api, hass):
        sensor = OnyxSensorWeatherSunBrightnessSink(
            api, "UTC", "name", DeviceType.WEATHER, "uuid"
        )
        sensor.hass = hass
        yield sensor

    def test_icon(self, entity):
        assert entity.icon == "mdi:weather-sunset-down"

    def test_name(self, entity):
        assert entity.name == "name Sun Brightness Sink"

    def test_unique_id(self, entity):
        assert entity.unique_id == "uuid/SunBrightnessSink"

    def test_device_class(self, entity):
        assert entity.device_class == SensorDeviceClass.ILLUMINANCE

    def test_suggested_display_precision(self, entity):
        assert entity.suggested_display_precision == 0

    def test_unit_of_measurement(self, entity):
        assert entity.unit_of_measurement == LIGHT_LUX

    def test_state(self, api, entity, device):
        api.device.return_value = device
        assert entity.state == 2
        assert api.device.called
