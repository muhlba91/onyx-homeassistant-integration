"""Test for ONYX integration init, setup and teardown."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_FORCE_UPDATE,
)

from custom_components.hella_onyx import (
    DOMAIN,
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
    async_migrate_entry,
)
from custom_components.hella_onyx.const import (
    CONF_FINGERPRINT,
    CONF_LOCAL_ADDRESS,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    CONF_ADDITIONAL_DELAY,
    CONF_INTERPOLATION_FREQUENCY,
)
from custom_components.hella_onyx.models import OnyxData


@pytest.fixture
def mock_config_entry():
    entry = ConfigEntry(
        version=3,
        minor_version=1,
        domain=DOMAIN,
        title="test_fingerprint",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        source="user",
        unique_id="fingerprint_123",
        options={
            CONF_LOCAL_ADDRESS: "192.168.1.50",
            CONF_SCAN_INTERVAL: 60,
            CONF_INTERPOLATION_FREQUENCY: 5,
            CONF_ADDITIONAL_DELAY: 1000,
            CONF_MIN_DIM_DURATION: 200,
            CONF_MAX_DIM_DURATION: 2000,
            CONF_FORCE_UPDATE: True,
        },
        discovery_keys={},
        subentries_data={},
    )
    return entry


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_and_unload(
    mock_api_connector_class, mock_config_entry
):
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="Europe/Vienna")
    mock_api.events = MagicMock()
    mock_api_connector_class.return_value = mock_api

    task_mock = MagicMock()
    hass.async_create_background_task.return_value = task_mock
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_setup_entry(hass, mock_config_entry)
    assert result is True
    assert isinstance(mock_config_entry.runtime_data, OnyxData)
    assert mock_config_entry.runtime_data.api == mock_api
    assert mock_config_entry.runtime_data.timezone == "Europe/Vienna"
    assert hass.async_create_background_task.called

    unload_result = await async_unload_entry(hass, mock_config_entry)
    assert unload_result is True


@pytest.mark.asyncio
async def test_async_reload_entry(mock_config_entry):
    hass = MagicMock()
    hass.config_entries.async_reload = AsyncMock()
    await async_reload_entry(hass, mock_config_entry)
    hass.config_entries.async_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_async_migrate_entry_v1():
    hass = MagicMock()
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
            CONF_SCAN_INTERVAL: 30,
            CONF_MIN_DIM_DURATION: 100,
            CONF_MAX_DIM_DURATION: 1500,
            CONF_FORCE_UPDATE: True,
        },
        source="user",
        unique_id="test",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    result = await async_migrate_entry(hass, entry)
    assert result is True
    assert hass.config_entries.async_update_entry.called


@pytest.mark.asyncio
async def test_async_migrate_entry_v2():
    hass = MagicMock()
    entry = ConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
            CONF_LOCAL_ADDRESS: "192.168.1.1",
            CONF_SCAN_INTERVAL: 30,
            CONF_INTERPOLATION_FREQUENCY: 3,
            CONF_MIN_DIM_DURATION: 100,
            CONF_MAX_DIM_DURATION: 1500,
            CONF_FORCE_UPDATE: False,
        },
        source="user",
        unique_id="test",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    result = await async_migrate_entry(hass, entry)
    assert result is True
    assert hass.config_entries.async_update_entry.called
