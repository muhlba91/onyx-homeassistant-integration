"""API connector for the ONYX integration."""
import logging
from datetime import timedelta
from random import uniform

from aiohttp import ClientSession, ClientTimeout
import async_timeout
import asyncio

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from onyx_client.client import create
from onyx_client.data.device_command import DeviceCommand
from onyx_client.enum.action import Action

from .const import DOMAIN, MAX_BACKOFF_TIME

_LOGGER = logging.getLogger(__name__)


class APIConnector(DataUpdateCoordinator):
    """API connector for an ONYX.CENTER."""

    def __init__(self, hass, scan_interval, fingerprint, token):
        """Initialize the connector."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=0, immediate=True
            ),
        )
        self.hass = hass
        self.fingerprint = fingerprint
        self.token = token
        self.data = {}
        self.groups = {}
        self.__client = None

    def _client(self):
        if self.__client is None:
            self.__client = self._new_client(async_get_clientsession(self.hass))
        return self.__client

    def _new_client(self, session):
        return create(
            fingerprint=self.fingerprint,
            access_token=self.token,
            client_session=session,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            return await self.update()

    async def get_timezone(self):
        """Gets the ONYX.CENTER timezone."""
        date_information = await self._client().date_information()
        if date_information is not None:
            return date_information.timezone
        else:
            return "UTC"

    async def update(self):
        """Update all entities."""
        devices = await self._client().devices(include_details=True)
        self.data = {device.identifier: device for device in devices}
        groups = await self._client().groups()
        self.groups = {group.identifier: group for group in groups}

    def device(self, uuid: str):
        """Get the Device associated with the provided UUID."""
        if uuid in self.data:
            return self.data[uuid]
        raise UnknownStateException("UNKNOWN_DEVICE")

    async def update_device(self, uuid: str):
        """Update the given entity."""
        device = await self._client().device(uuid)
        self.data[device.identifier] = device
        return device

    def updated_device(self, device):
        """Update the given device."""
        _LOGGER.debug("received device update %s (%s)", device.identifier, device)
        if device.identifier in self.data:
            self.data[device.identifier].update_with(device)

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

    async def events(self, force_update: bool = False):
        """Listen and process device events."""
        while True:
            backoff = int(uniform(0, MAX_BACKOFF_TIME) * 60)
            try:
                async with ClientSession(
                    timeout=ClientTimeout(
                        total=None, connect=None, sock_connect=None, sock_read=None
                    )
                ) as session:
                    client = self._new_client(session)
                    async for device in client.events(force_update):
                        self.updated_device(device)
                        self.async_set_updated_data(self.data)
            except Exception as ex:
                _LOGGER.error(
                    "connection reset: %s, restarting with backoff of %s seconds (%s)",
                    ex,
                    backoff,
                    self._backoff,
                )
            if self._backoff:
                await asyncio.sleep(backoff)
            else:
                break


class CommandException(Exception):
    """Exception for a failed command."""

    def __init__(self, msg: str, uuid: str):
        super().__init__(msg)
        _LOGGER.error("command errored: %s for id %s", msg, uuid)


class UnknownStateException(Exception):
    """Exception if the shutter is unknown."""

    def __init__(self, msg):
        super().__init__(msg)
        _LOGGER.error("unknown state: %s", msg)
