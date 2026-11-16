"""The ONYX identify button."""

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.const import EntityCategory
from onyx_client.enum.action import Action

from ..sensors.onyx_entity import OnyxEntity

_LOGGER = logging.getLogger(__name__)


class OnyxButtonIdentify(OnyxEntity, ButtonEntity):
    """ONYX Identify Button (winks the device, disabled by default)."""

    _attr_entity_registry_enabled_default = False

    @property
    def name(self) -> str:
        """Return the display name of the button."""
        return f"{self._name} Identify"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the button."""
        return f"{self._uuid}/Identify"

    @property
    def icon(self) -> str | None:
        """Icon to use in the frontend, if any (the icon of the device class)."""
        return None

    @property
    def device_class(self) -> ButtonDeviceClass | None:
        """Return the class of this button."""
        return ButtonDeviceClass.IDENTIFY

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Wink the device."""
        _LOGGER.debug("winking device %s", self._uuid)
        await self.api.send_device_command_action(self._uuid, Action.WINK)
