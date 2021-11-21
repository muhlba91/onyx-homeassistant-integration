"""The ONYX entity."""

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from onyx_client.enum.device_type import DeviceType

from .api_connector import APIConnector
from .const import DOMAIN


class OnyxEntity(CoordinatorEntity):
    """An ONYX entity."""

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        coordinator: DataUpdateCoordinator,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a ONYX entity."""
        super().__init__(coordinator)
        self.api = api
        self.timezone = timezone
        self._name = name
        self._type = device_type
        self._uuid = uuid

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:window-shutter"

    @property
    def device_info(self):
        """Return the device information of the entity."""
        return {
            "identifiers": {(DOMAIN, self._uuid)},
            "name": self._name,
            "manufacturer": "Hella",
            "model": self._type.string(),
        }

    @property
    def _device(self):
        """Get the underlying device."""
        return self.api.device(self._uuid)
