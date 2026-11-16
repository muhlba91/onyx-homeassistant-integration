"""The ONYX automation switch."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from onyx_client.data.automation import Automation

from ..api_connector import APIConnector
from ..const import AUTOMATION_CONTEXT
from ..sensors.onyx_center import center_device_info

_LOGGER = logging.getLogger(__name__)


class OnyxAutomationSwitch(CoordinatorEntity, SwitchEntity):
    """Enables or disables an automation of the ONYX.CENTER (experimental).

    Disabled by default: disabling a safety automation, e.g. the wind
    protection, leaves the shading products unprotected. The switch belongs to
    the ONYX.CENTER device and is unavailable once the automation is removed.
    """

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, api: APIConnector, identifier: str):
        """Initialize an automation switch."""
        super().__init__(api, context=AUTOMATION_CONTEXT)
        self.api = api
        self._identifier = identifier

    @property
    def name(self) -> str:
        """Return the display name of the switch."""
        return f"{self._label} Automation"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return f"{self.api.config.fingerprint}/Automation/{self._identifier}"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:robot"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the ONYX.CENTER."""
        return center_device_info(self.api)

    @property
    def available(self) -> bool:
        """Return if the automation is known to the ONYX.CENTER."""
        return super().available and self._automation is not None

    @property
    def is_on(self) -> bool | None:
        """Return whether the automation is enabled."""
        automation = self._automation
        return automation.enabled if automation else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the identity of the automation."""
        automation = self._automation
        if automation is None:
            return None
        return {
            "automation_id": automation.identifier,
            "automation_type": automation.automation_type,
            "emoji": automation.emoji,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the automation."""
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the automation, which cancels its commands."""
        await self._set_enabled(False)

    async def _set_enabled(self, enabled: bool) -> None:
        if not await self.api.set_automation_enabled(self._identifier, enabled):
            raise HomeAssistantError(
                f"the ONYX.CENTER did not {'enable' if enabled else 'disable'} "
                f"the automation {self._label}"
            )

    @property
    def _automation(self) -> Automation | None:
        """Get the automation, or None if it is no longer known."""
        return self.api.automation(self._identifier)

    @property
    def _label(self) -> str:
        """The name of the automation, else of its device, else its type.

        Automations of a single device, e.g. the wind protection of a weather
        sensor, often have no name; the ONYX App shows the device's name.
        """
        automation = self._automation
        if automation is not None and automation.name:
            return automation.name
        device = next(
            (
                device
                for identifier, device in self.api.devices.items()
                if identifier in self._identifier
            ),
            None,
        )
        if device is not None:
            return device.name
        if automation is not None and automation.automation_type:
            return automation.automation_type
        return self._identifier
