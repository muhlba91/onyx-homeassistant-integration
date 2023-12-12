"""API connector for the ONYX integration."""
import logging

from aiohttp import ClientSession, ClientTimeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from onyx_client.client import create
from onyx_client.data.device_command import DeviceCommand
from onyx_client.enum.action import Action

_LOGGER = logging.getLogger(__name__)


class APIConnector:
    """API connector for an ONYX.CENTER."""

    def __init__(self, hass, fingerprint, token):
        """Initialize the connector."""
        self.hass = hass
        self.fingerprint = fingerprint
        self.token = token
        self.devices = {}
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
        self.devices = {device.identifier: device for device in devices}
        groups = await self._client().groups()
        self.groups = {group.identifier: group for group in groups}

    def device(self, uuid: str):
        """Get the Device associated with the provided UUID."""
        if uuid in self.devices:
            return self.devices[uuid]
        raise UnknownStateException("UNKNOWN_DEVICE")

    async def update_device(self, uuid: str):
        """Update the given entity."""
        device = await self._client().device(uuid)
        self.devices[device.identifier] = device
        return device

    def updated_device(self, device):
        """Update the given device."""
        _LOGGER.debug("Received device update %s (%s)", device.identifier, device)
        self.devices[device.identifier].update_with(device)

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
        """Listen for events."""
        async with ClientSession(
            timeout=ClientTimeout(
                total=None, connect=None, sock_connect=None, sock_read=None
            )
        ) as session:
            client = self._new_client(session)
        async for device in client.events(force_update):
            yield device


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
