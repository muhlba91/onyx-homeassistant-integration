"""The ONYX entity."""

import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from onyx_client.enum.device_type import DeviceType

from ..api_connector import APIConnector, UnknownStateException
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OnyxEntity(CoordinatorEntity):
    """An ONYX entity."""

    def __init__(
        self,
        api: APIConnector,
        timezone: str,
        name: str,
        device_type: DeviceType,
        uuid: str,
    ):
        """Initialize a ONYX entity."""
        super().__init__(api)
        self.api = api
        self.timezone = timezone
        self._name = name
        self._type = device_type
        self._uuid = uuid

    @callback
    def _handle_coordinator_update(self) -> None:
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:help"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._uuid)},
            name=self._name,
            manufacturer="Hella",
            model=self._type.string(),
        )

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._uuid}/Device"

    @property
    def _device(self):
        """Get the underlying device, or None if it is no longer known."""
        try:
            return self.api.device(self._uuid)
        except UnknownStateException:
            _LOGGER.warning(
                "device %s is no longer available; skipping state update",
                self._uuid,
            )
            return None
