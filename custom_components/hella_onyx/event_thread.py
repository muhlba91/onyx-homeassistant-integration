"""ONYX API event thread."""
import asyncio
import logging
import threading
from random import uniform

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api_connector import APIConnector, UnknownStateException
from .const import MAX_BACKOFF_TIME

_LOGGER = logging.getLogger(__name__)


class EventThread(threading.Thread):
    """The event thread for asynchronous updates."""

    def __init__(
        self,
        api: APIConnector,
        coordinator: DataUpdateCoordinator,
        backoff: bool = True,
    ):
        threading.Thread.__init__(self, name="HellaOnyx")
        self._api = api
        self._coordinator = coordinator
        self._backoff = backoff

    async def _update(self):
        """Listen for updates."""
        while True:
            try:
                async for device in self._api.listen_events():
                    try:
                        self._api.device(device.identifier).update_with(device)
                        self._coordinator.async_set_updated_data(None)
                    except UnknownStateException:
                        _LOGGER.info("ignoring update for %s", device.identifier)
            except Exception as ex:
                _LOGGER.error("connection reset: %s, restarting: %s", ex, self._backoff)
            if self._backoff:
                backoff = int(uniform(0, MAX_BACKOFF_TIME) * 60)
                await asyncio.sleep(backoff)
            else:
                break

    def run(self):
        """Start the thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self._update())
        loop.run_forever()
