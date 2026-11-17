"""Helpers for the ONYX tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from onyx_client.data.automation import Automation
from onyx_client.data.date_information import DateInformation
from onyx_client.data.update_status import UpdateStatus
from onyx_client.enum.verify_result import VerifyResult
from onyx_client.group.group import Group
from onyx_client.stream.events import Snapshot
from onyx_client.utils.mapper import init_device

MODULE = "custom_components.hella_onyx.api_connector"


def shutter(identifier: str, position: int = 0):
    return init_device(
        identifier,
        {
            "name": identifier,
            "type": "rollershutter",
            "properties": {"actual_position": {"value": position, "maximum": 100}},
        },
    )


def automation(identifier: str, enabled: bool = True):
    return Automation(identifier, identifier, None, "wind", enabled)


def snapshot(*devices, automations=()):
    return Snapshot(
        {device.identifier: device for device in devices},
        {"group": Group("group", "Group", ["a"])},
        list(automations),
        UpdateStatus("2.13.4"),
    )


class FakeClient:
    """A client streaming the given events, then staying connected."""

    def __init__(self, events=(), error=None):
        self.events = list(events)
        self.error = error
        self.verify = AsyncMock(return_value=VerifyResult.OK)
        self.resync = MagicMock()
        self.close = AsyncMock()
        self.now = MagicMock(return_value=1.5)
        self.send_command = AsyncMock(return_value=True)
        self.date_information = AsyncMock(
            return_value=DateInformation(0, "Europe/Vienna", 0)
        )

    async def stream(self):
        for event in self.events:
            yield event
        if self.error is not None:
            raise self.error
        await asyncio.Event().wait()
