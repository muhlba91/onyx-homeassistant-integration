"""Test for the ONYX Update Platform."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.hella_onyx import DOMAIN
from custom_components.hella_onyx.models import OnyxData
from custom_components.hella_onyx.update import async_setup_entry


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
    config_entry.runtime_data = OnyxData(api=api, config=MagicMock(), timezone="UTC")
    add_entities = MagicMock()

    await async_setup_entry(mock_hass, config_entry, add_entities)
    entities = add_entities.call_args.args[0]
    assert [entity.unique_id for entity in entities] == ["finger/Update"]
    assert entities[0].api == api
