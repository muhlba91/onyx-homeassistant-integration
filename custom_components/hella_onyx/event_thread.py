"""ONYX API event thread."""
import asyncio
import logging
import threading

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api_connector import APIConnector, UnknownStateException

_LOGGER = logging.getLogger(__name__)


class EventThread(threading.Thread):
    """The event thread for asynchronous updates."""

    def __init__(self, api: APIConnector, coordinator: DataUpdateCoordinator):
        threading.Thread.__init__(self, name="HellaOnyx")
        self._api = api
        self._coordinator = coordinator

    async def _update(self):
        """Listen for updates."""
        async for device in self._api.listen_events():
            try:
                self._api.device(device.identifier).update_with(device)
                self._coordinator.async_set_updated_data(None)
            except UnknownStateException:
                _LOGGER.info("ignoring update for %s", device.identifier)

    def run(self):
        """Start the thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self._update())
        loop.run_forever()
