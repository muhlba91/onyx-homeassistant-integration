"""API connector for the ONYX integration."""

import asyncio
import logging
import time
from contextlib import aclosing
from datetime import timedelta

from aiohttp import ClientResponseError
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from onyx_client.client import create
from onyx_client.data.automation import Automation
from onyx_client.data.device_command import DeviceCommand
from onyx_client.data.update_status import UpdateStatus
from onyx_client.enum.action import Action
from onyx_client.enum.verify_result import VerifyResult
from onyx_client.stream.events import (
    AutomationsChanged,
    DeviceAdded,
    DeviceChanged,
    DeviceRemoved,
    GroupsChanged,
    Resynced,
    Snapshot,
    UpdateChanged,
)

from .configuration import Configuration
from .const import (
    AUTOMATION_CONTEXT,
    DOMAIN,
    SNAPSHOT_TIMEOUT,
    STREAM_CHECK_INTERVAL,
    STREAM_RESTART_DELAY,
    STREAM_SILENCE_TIMEOUT,
    UPDATE_CONTEXT,
)

_LOGGER = logging.getLogger(__name__)


class APIConnector(DataUpdateCoordinator):
    """API connector for an ONYX.CENTER.

    The state comes from the client's event stream. Every scan interval
    resyncs the stream, which replaces the state with a fresh snapshot. If
    the stream fails unexpectedly, the entities become unavailable and the
    stream restarts every STREAM_RESTART_DELAY until it succeeds. The client
    reconnects a dropped stream by itself; if no event, including the
    pulse, arrives for STREAM_SILENCE_TIMEOUT, the entities become
    unavailable until the next event.
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
        self._known_automations = None
        self._snapshot = asyncio.Event()
        self._stream_task = None
        self._restart_unsub = None
        self._restarting = False
        self._last_event = None
        self._check_unsub = None
        self._resync_requested = False
        self._silent = False
        # reconnects the integration did not request, e.g. a center restart
        self.stream_drops = 0
        self._update_lock = asyncio.Lock()
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

    @property
    def automations(self) -> list[Automation]:
        """Return all automations in the order of the ONYX App."""
        return self.data["automations"]

    def automation(self, identifier: str) -> Automation | None:
        """Get the automation with the provided identifier, if known."""
        return next(
            (
                automation
                for automation in self.automations
                if automation.identifier == identifier
            ),
            None,
        )

    @property
    def update_status(self) -> UpdateStatus | None:
        """Return the software update status, if known."""
        return self.data["update"]

    def now(self) -> float:
        """Return the current time of the ONYX.CENTER as UNIX timestamp."""
        return self._client().now()

    async def _async_update_data(self):
        """Start the event stream, or resync it if it is running."""
        # a restart and a scheduled refresh must not start two streams
        async with self._update_lock:
            if self._stream_task is not None and not self._stream_task.done():
                silent = self._stream_silent()
                # a resync during an outage merges into the pending reconnect
                self._resync_requested = not silent
                self._client().resync()
                if silent:
                    # keep the entities unavailable until the next snapshot
                    raise UpdateFailed("no events from the ONYX.CENTER")
                return self.data

            self._cancel_restart()
            try:
                await self._start_stream()
            except UpdateFailed:
                if self._restarting:
                    self._schedule_restart()
                raise
            self._restarting = False
            return self.data

    async def _start_stream(self):
        """Verify the connection and wait for the first snapshot of a new stream."""
        result = await self._client().verify()
        if result == VerifyResult.UNAUTHORIZED:
            raise ConfigEntryAuthFailed("the access token was rejected")
        if result == VerifyResult.VERSION_UNSUPPORTED:
            raise ConfigEntryError(
                "the ONYX.CENTER does not support API v6, update its firmware"
            )
        if result != VerifyResult.OK:
            raise UpdateFailed("the ONYX.CENTER is unreachable")
        if self._shutdown_requested:
            raise UpdateFailed("the integration is shutting down")

        self._snapshot.clear()
        self._last_event = time.monotonic()
        self._resync_requested = False
        self._silent = False
        self._stream_task = self.hass.async_create_background_task(
            self._stream(), name=f"{DOMAIN}_stream"
        )
        try:
            async with asyncio.timeout(SNAPSHOT_TIMEOUT):
                await self._snapshot.wait()
        except TimeoutError as ex:
            await self._stop_stream()
            raise UpdateFailed("no snapshot received") from ex
        if self._check_unsub is None and not self._shutdown_requested:
            self._check_unsub = async_track_time_interval(
                self.hass,
                self._check_stream,
                timedelta(seconds=STREAM_CHECK_INTERVAL),
                name=f"{DOMAIN}_stream_check",
            )

    async def async_shutdown(self):
        """Stop the event stream when the config entry is unloaded."""
        await super().async_shutdown()
        await self._stop_stream()

    async def _stop_stream(self):
        """Stop the event stream and a pending restart."""
        # cancel the task first, so its failure while closing is not restarted
        task, self._stream_task = self._stream_task, None
        if task is not None:
            task.cancel()
        if self.__client is not None:
            # a closed client cannot stream again
            await self.__client.close()
            self.__client = None
        self._cancel_restart()
        if self._check_unsub is not None:
            self._check_unsub()
            self._check_unsub = None

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

    async def set_automation_enabled(self, identifier: str, enabled: bool) -> bool:
        """Enable or disable an automation; disabling cancels its commands."""
        _LOGGER.info(
            "%s automation %s", "enabling" if enabled else "disabling", identifier
        )
        client = self._client()
        switch = client.enable_automation if enabled else client.disable_automation
        automation = await switch(identifier)
        if automation is None:
            return False
        # show the new state before the stream reports it
        self.data["automations"] = [
            automation if known.identifier == identifier else known
            for known in self.automations
        ]
        self._update_device_listeners(AUTOMATION_CONTEXT)
        return True

    async def install_update(self) -> bool:
        """Install the available software update, which restarts the ONYX.CENTER."""
        _LOGGER.info("installing the software update of the ONYX.CENTER")
        return await self._client().install_update() is not None

    async def _stream(self):
        """Consume the event stream until it is cancelled or rejected."""
        try:
            async with aclosing(self._client().stream()) as events:
                async for event in events:
                    self._handle_event(event)
        except ClientResponseError as ex:
            if asyncio.current_task().cancelling():
                return  # stopped by _stop_stream while failing
            # the client raises only for rejected credentials (401/403)
            _LOGGER.error("event stream rejected the credentials: %s", ex)
            self.async_set_update_error(ex)
            if self.config_entry is not None:
                self.config_entry.async_start_reauth(self.hass)
        except Exception as ex:
            if asyncio.current_task().cancelling():
                return  # stopped by _stop_stream while failing
            # the client reconnects by itself, so this is unexpected
            _LOGGER.exception(
                "event stream failed, restarting in %s seconds", STREAM_RESTART_DELAY
            )
            self.async_set_update_error(ex)
            self._restarting = True
            self._schedule_restart()

    def _schedule_restart(self):
        """Restart the event stream after STREAM_RESTART_DELAY."""
        self._cancel_restart()
        if self._shutdown_requested:
            return
        self._restart_unsub = async_call_later(
            self.hass, STREAM_RESTART_DELAY, self._handle_stream_restart
        )

    def _cancel_restart(self):
        """Cancel the pending restart, if any."""
        if self._restart_unsub is not None:
            self._restart_unsub()
            self._restart_unsub = None

    def _stream_silent(self) -> bool:
        """Return whether no event arrived for STREAM_SILENCE_TIMEOUT."""
        return (
            self._last_event is not None
            and time.monotonic() - self._last_event > STREAM_SILENCE_TIMEOUT
        )

    @callback
    def _check_stream(self, _now):
        """Mark the entities unavailable while the running stream is silent."""
        if self._stream_task is None or self._stream_task.done():
            return  # a failed stream is handled by its restart
        if self.last_update_success and self._stream_silent():
            # one warning instead of the coordinator's error, e.g. during an update
            _LOGGER.warning(
                "no events from the ONYX.CENTER for %s seconds, "
                "entities are unavailable until it is back",
                STREAM_SILENCE_TIMEOUT,
            )
            self._silent = True
            self.last_update_success = False
            self.last_exception = UpdateFailed("no events from the ONYX.CENTER")
            self.async_update_listeners()

    @callback
    def _handle_stream_restart(self, _now):
        """Restart the failed event stream with a refresh."""
        self._restart_unsub = None
        self.hass.async_create_background_task(
            self.async_request_refresh(), name=f"{DOMAIN}_stream_restart"
        )

    def _handle_event(self, event):
        """Apply a stream event to the data and notify the affected entities."""
        _LOGGER.debug("received event %s", type(event).__name__)
        self._last_event = time.monotonic()
        recovered = self._silent and not isinstance(event, Resynced)
        if recovered:
            # the snapshot following Resynced brings the fresh state
            _LOGGER.info("events from the ONYX.CENTER are back")
            self._silent = False
            self.last_update_success = True
        if isinstance(event, Resynced):
            if self._resync_requested:
                self._resync_requested = False
            else:
                self.stream_drops += 1
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
            self._check_new_automations(event.automations)
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
            self._check_new_automations(event.automations)
            self._update_device_listeners(AUTOMATION_CONTEXT)
        elif isinstance(event, UpdateChanged):
            self.data["update"] = event.update
            self._update_device_listeners(UPDATE_CONTEXT)
        if recovered and not isinstance(event, Snapshot):
            self.async_update_listeners()

    def _update_device_listeners(self, context: str):
        """Notify only the entities of the given device or other context."""
        for update_callback, listener_context in list(self._listeners.values()):
            if listener_context == context:
                update_callback()

    def _check_new_automations(self, automations: list[Automation]):
        """Reload the config entry once to add switches for new automations."""
        identifiers = {automation.identifier for automation in automations}
        if self._known_automations is None:
            self._known_automations = identifiers
        elif not identifiers <= self._known_automations:
            self._known_automations |= identifiers
            self._schedule_reload("new automations")

    def _reload(self, reason: str, devices: set):
        """Reload the config entry once to add entities for the new devices."""
        self._known_devices = (self._known_devices or set()) | devices
        self._schedule_reload(reason)

    def _schedule_reload(self, reason: str):
        """Reload the config entry."""
        _LOGGER.info("reloading %s: %s", DOMAIN, reason)
        if self.config_entry is not None:
            self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)


class CommandException(Exception):
    """Exception for a failed command."""

    def __init__(self, msg: str, uuid: str):
        super().__init__(msg)
        self.uuid = uuid
        _LOGGER.error("command errored: %s for id %s", msg, uuid)
