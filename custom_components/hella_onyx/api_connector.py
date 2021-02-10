"""API connector for the ONYX integration."""
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from onyx_client import create_client
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
        self.verify_tls = False
        self.devices = {}
        self.groups = {}

    def _client(self):
        session = async_get_clientsession(self.hass, self.verify_tls)
        return create_client(
            fingerprint=self.fingerprint,
            access_token=self.token,
            client_session=session,
        )

    async def update(self):
        """Update all entities."""
        client = self._client()
        devices = await client.devices(include_details=True)
        self.devices = {device.identifier: device for device in devices}
        groups = await client.groups()
        self.groups = {group.identifier: group for group in groups}

    def device(self, uuid: str):
        """Get the Device associated with the provided UUID."""
        if uuid in self.devices:
            return self.devices[uuid]
        raise UnknownStateException("UNKNOWN_DEVICE")

    async def update_device(self, uuid: str):
        """Update the given entity."""
        client = self._client()
        device = await client.device(uuid)
        self.devices[device.identifier] = device
        return device

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


class CommandException(Exception):
    """Exception for a failed command."""

    def __init__(self, msg: str, uuid: str):
        super().__init__(msg)
        _LOGGER.error("Command errored: %s for id %s", msg, uuid)


class UnknownStateException(Exception):
    """Exception if the shutter is unknown."""

    def __init__(self, msg):
        super().__init__(msg)
        _LOGGER.error("Unknown state: %s", msg)
