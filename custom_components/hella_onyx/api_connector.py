"""API connector for the ONYX integration."""

import asyncio
import logging
from contextlib import aclosing
from datetime import timedelta

from aiohttp import ClientResponseError
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from onyx_client.client import create
from onyx_client.data.device_command import DeviceCommand
from onyx_client.enum.action import Action
from onyx_client.enum.verify_result import VerifyResult
from onyx_client.stream.events import (
    AutomationsChanged,
    DeviceAdded,
    DeviceChanged,
    DeviceRemoved,
    GroupsChanged,
    Snapshot,
    UpdateChanged,
)

from .configuration import Configuration
from .const import DOMAIN, SNAPSHOT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class APIConnector(DataUpdateCoordinator):
    """API connector for an ONYX.CENTER.

    The state comes from the client's event stream. Every scan interval
    resyncs the stream, which replaces the state with a fresh snapshot.
    """

    def __init__(self, hass, config: Configuration, entry=None):
        """Initialize the connector."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=config.scan_interval),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=0, immediate=True
            ),
        )
        self.config = config
        self.data = {
            "devices": {},
            "groups": {},
            "automations": [],
            "update": None,
        }
        self._known_devices = None
        self._snapshot = asyncio.Event()
        self._stream_task = None
        self.__client = None

    def _client(self):
        if self.__client is None:
            self.__client = create(
                fingerprint=self.config.fingerprint,
                access_token=self.config.token,
                client_session=async_get_clientsession(self.hass),
                local_address=self.config.local_address,
            )
        return self.__client

    @property
    def devices(self):
        """Return all devices."""
        return self.data["devices"]

    @property
    def groups(self):
        """Return all groups."""
        return self.data["groups"]

    def now(self) -> float:
        """Return the current time of the ONYX.CENTER as UNIX timestamp."""
        return self._client().now()

    async def _async_update_data(self):
        """Start the event stream, or resync it if it is running."""
        if self._stream_task is not None and not self._stream_task.done():
            self._client().resync()
            return self.data

        result = await self._client().verify()
        if result == VerifyResult.UNAUTHORIZED:
            raise ConfigEntryAuthFailed("the access token was rejected")
        if result == VerifyResult.VERSION_UNSUPPORTED:
            raise ConfigEntryError(
                "the ONYX.CENTER does not support API v6, update its firmware"
            )
        if result != VerifyResult.OK:
            raise UpdateFailed("the ONYX.CENTER is unreachable")

        self._snapshot.clear()
        self._stream_task = self.hass.async_create_background_task(
            self._stream(), name=f"{DOMAIN}_stream"
        )
        try:
            async with asyncio.timeout(SNAPSHOT_TIMEOUT):
                await self._snapshot.wait()
        except TimeoutError as ex:
            await self._stop_stream()
            raise UpdateFailed("no snapshot received") from ex
        return self.data

    async def async_shutdown(self):
        """Stop the event stream when the config entry is unloaded."""
        await super().async_shutdown()
        await self._stop_stream()

    async def _stop_stream(self):
        """Stop the event stream."""
        if self.__client is not None:
            # a closed client cannot stream again
            await self.__client.close()
            self.__client = None
        if self._stream_task is not None:
            self._stream_task.cancel()
            self._stream_task = None

    async def get_timezone(self):
        """Gets the ONYX.CENTER timezone."""
        date_information = await self._client().date_information()
        if date_information is not None:
            return date_information.timezone
        else:
            return "UTC"

    def device(self, uuid: str):
        """Get the device associated with the provided UUID, if known."""
        return self.devices.get(uuid)

    async def send_device_command_action(self, uuid: str, action: Action):
        _LOGGER.info("executing %s for device %s", action.string(), uuid)
        success = await self._client().send_command(uuid, DeviceCommand(action=action))
        if not success:
            raise CommandException("ONYX_ACTION_ERROR", uuid)

    async def send_device_command_properties(self, uuid: str, properties: dict):
        _LOGGER.info("executing %s for device %s", properties, uuid)
        success = await self._client().send_command(
            uuid, DeviceCommand(properties=properties)
        )
        if not success:
            raise CommandException("ONYX_ACTION_ERROR", uuid)

    async def _stream(self):
        """Consume the event stream until it is cancelled or rejected."""
        try:
            async with aclosing(self._client().stream()) as events:
                async for event in events:
                    self._handle_event(event)
        except ClientResponseError as ex:
            # the client raises only for rejected credentials (401/403)
            _LOGGER.error("event stream rejected the credentials: %s", ex)
            if self.config_entry is not None:
                self.config_entry.async_start_reauth(self.hass)
        except Exception:
            _LOGGER.exception("event stream failed, restarting with the next scan")

    def _handle_event(self, event):
        """Apply a stream event to the data and notify the affected entities."""
        _LOGGER.debug("received event %s", type(event).__name__)
        if isinstance(event, Snapshot):
            self.data = {
                "devices": event.devices,
                "groups": event.groups,
                "automations": event.automations,
                "update": event.update,
            }
            if self._known_devices is None:
                self._known_devices = set(event.devices)
            elif not set(event.devices) <= self._known_devices:
                self._reload("new devices in snapshot", set(event.devices))
            self._snapshot.set()
            self.async_update_listeners()
        elif isinstance(event, DeviceAdded):
            identifier = event.device.identifier
            self.devices[identifier] = event.device
            if identifier in (self._known_devices or ()):
                self._update_device_listeners(identifier)
            else:
                self._reload(f"device {identifier} added", {identifier})
        elif isinstance(event, DeviceChanged):
            self.devices[event.device.identifier] = event.device
            self._update_device_listeners(event.device.identifier)
        elif isinstance(event, DeviceRemoved):
            self.devices.pop(event.identifier, None)
            self._update_device_listeners(event.identifier)
        elif isinstance(event, GroupsChanged):
            self.data["groups"] = event.groups
        elif isinstance(event, AutomationsChanged):
            self.data["automations"] = event.automations
        elif isinstance(event, UpdateChanged):
            self.data["update"] = event.update

    def _update_device_listeners(self, uuid: str):
        """Notify only the entities of the given device."""
        for update_callback, context in list(self._listeners.values()):
            if context == uuid:
                update_callback()

    def _reload(self, reason: str, devices: set):
        """Reload the config entry once to add entities for the new devices."""
        _LOGGER.info("reloading %s: %s", DOMAIN, reason)
        self._known_devices = (self._known_devices or set()) | devices
        if self.config_entry is not None:
            self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)


class CommandException(Exception):
    """Exception for a failed command."""

    def __init__(self, msg: str, uuid: str):
        super().__init__(msg)
        self.uuid = uuid
        _LOGGER.error("command errored: %s for id %s", msg, uuid)
