"""The ONYX.CENTER update entity."""

import logging
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from onyx_client.data.update_status import UpdateStatus

from ..api_connector import APIConnector
from ..const import UPDATE_CONTEXT, UPDATE_INSTALL_TIMEOUT
from ..sensors.onyx_center import center_device_info

_LOGGER = logging.getLogger(__name__)


class OnyxUpdate(CoordinatorEntity, UpdateEntity):
    """The software update of the ONYX.CENTER.

    An update is available while the ONYX.CENTER reports one; its versions
    are not compared. The ONYX.CENTER checks for updates by itself, this
    entity never triggers a check. Installing restarts the ONYX.CENTER; the
    entity stays available and in progress until the ONYX.CENTER reports a
    new version or is back after the restart, at most UPDATE_INSTALL_TIMEOUT.
    """

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )
    _attr_title = "ONYX.CENTER"

    def __init__(self, api: APIConnector):
        """Initialize the update entity."""
        super().__init__(api, context=UPDATE_CONTEXT)
        self.api = api
        self._installing: UpdateStatus | None = None
        self._install_drops = 0
        self._install_unsub = None

    async def async_will_remove_from_hass(self) -> None:
        """Cancel the pending installation timeout."""
        self._cancel_install_timeout()
        await super().async_will_remove_from_hass()

    @property
    def name(self) -> str:
        """Return the display name of the entity."""
        return "ONYX.CENTER Update"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the entity."""
        return f"{self.api.config.fingerprint}/Update"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the ONYX.CENTER."""
        status = self._status
        return center_device_info(self.api, status.current if status else None)

    @property
    def available(self) -> bool:
        """Return if the status is known; also while an installation restarts."""
        return self._status is not None and (
            super().available or self._installing is not None
        )

    @property
    def installed_version(self) -> str | None:
        """Return the installed software version."""
        status = self._status
        return status.current if status else None

    @property
    def latest_version(self) -> str | None:
        """Return the available version, or the installed one if there is none."""
        status = self._status
        if status is None:
            return None
        return status.available_version or status.current

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Return if an update is available; the versions are not semantic."""
        status = self._status
        return status is not None and status.available_version is not None

    @property
    def in_progress(self) -> bool:
        """Return if an update is transferred or installed."""
        status = self._status
        return self._installing is not None or (
            status is not None and status.progress is not None
        )

    @property
    def update_percentage(self) -> float | None:
        """Return the transferred percentage of the update, if transferring."""
        status = self._status
        if status is None or status.progress is None:
            return None
        return round(status.progress * 100, 1)

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install the available update, which restarts the ONYX.CENTER."""
        status = self._status
        drops = self.api.stream_drops
        if not await self.api.install_update():
            raise HomeAssistantError("the ONYX.CENTER did not start the update")
        self._installing = status
        self._install_drops = drops
        self._cancel_install_timeout()
        self._install_unsub = async_call_later(
            self.hass, UPDATE_INSTALL_TIMEOUT, self._handle_install_timeout
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """End the installation once the ONYX.CENTER is back or updated."""
        installing = self._installing
        status = self._status
        if installing is not None and status is not None:
            restarted = (
                self.api.stream_drops > self._install_drops
                and self.api.last_update_success
            )
            if restarted or status.current != installing.current:
                self._end_install()
        self._update_device_version()
        super()._handle_coordinator_update()

    @callback
    def _handle_install_timeout(self, _now) -> None:
        """End an installation which did not change the reported status."""
        self._install_unsub = None
        _LOGGER.warning(
            "the ONYX.CENTER did not report a new version within %s seconds",
            UPDATE_INSTALL_TIMEOUT,
        )
        self._end_install()
        self.async_write_ha_state()

    def _update_device_version(self) -> None:
        """Update the version of the ONYX.CENTER device after an update."""
        status = self._status
        device = self.device_entry
        if status is None or device is None or device.sw_version == status.current:
            return
        dr.async_get(self.hass).async_update_device(
            device.id, sw_version=status.current
        )

    def _end_install(self) -> None:
        """Stop showing the installation in progress."""
        self._installing = None
        self._cancel_install_timeout()

    def _cancel_install_timeout(self) -> None:
        """Cancel the pending installation timeout."""
        if self._install_unsub is not None:
            self._install_unsub()
            self._install_unsub = None

    @property
    def _status(self) -> UpdateStatus | None:
        """Return the update status, if known."""
        return self.api.update_status
