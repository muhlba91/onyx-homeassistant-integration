"""Test for the ONYX Switch Platform."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from onyx_client.data.automation import Automation

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.models import OnyxData
from custom_components.hella_onyx.switch import async_setup_entry


@patch("homeassistant.core.HomeAssistant")
@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass):
    config_entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="entry",
        data={},
        source="source",
        unique_id="onyx",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    api = MagicMock()
    api.config.fingerprint = "finger"
    api.automations = [
        Automation("a", "A", None, None, True),
        Automation("b", None, None, None, False),
    ]
    config_entry.runtime_data = OnyxData(api=api, config=MagicMock(), timezone="UTC")
    add_entities = MagicMock()

    await async_setup_entry(mock_hass, config_entry, add_entities)
    entities = add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == [
        "finger/Automation/a",
        "finger/Automation/b",
    ]
    assert entities[0].api == api
