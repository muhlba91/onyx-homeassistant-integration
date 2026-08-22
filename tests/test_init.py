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
    PLATFORMS,
)
from custom_components.hella_onyx.const import (
    CONF_FINGERPRINT,
    CONF_LOCAL_ADDRESS,
    CONF_MIN_DIM_DURATION,
    CONF_MAX_DIM_DURATION,
    CONF_ADDITIONAL_DELAY,
    CONF_INTERPOLATION_FREQUENCY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_INTERPOLATION_FREQUENCY,
    DEFAULT_ADDITIONAL_DELAY,
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
            CONF_SCAN_INTERVAL: 120,
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
    mock_api_connector_class.assert_called_once()
    call_args, call_kwargs = mock_api_connector_class.call_args
    assert call_args[0] == hass
    config = call_args[1]
    assert config.fingerprint == "fingerprint_123"
    assert config.token == "token_123"
    assert config.local_address == "192.168.1.50"
    assert config.scan_interval == 120
    assert config.interpolation_frequency == 5
    assert config.additional_delay == 1000
    assert config.min_dim_duration == 200
    assert config.max_dim_duration == 2000
    assert config.force_update is True
    assert call_args[2] == mock_config_entry
    assert isinstance(mock_config_entry.runtime_data, OnyxData)
    assert mock_config_entry.runtime_data.api == mock_api
    assert mock_config_entry.runtime_data.timezone == "Europe/Vienna"
    assert hass.async_create_background_task.called

    unload_result = await async_unload_entry(hass, mock_config_entry)
    assert unload_result is True
    hass.config_entries.async_unload_platforms.assert_called_once_with(
        mock_config_entry, PLATFORMS
    )


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
    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        options={
            CONF_SCAN_INTERVAL: 30,
            CONF_MIN_DIM_DURATION: 100,
            CONF_MAX_DIM_DURATION: 1500,
            CONF_FORCE_UPDATE: True,
        },
        version=2,
        minor_version=1,
    )


@pytest.mark.asyncio
async def test_async_migrate_entry_v1_defaults():
    hass = MagicMock()
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        source="user",
        unique_id="test",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    result = await async_migrate_entry(hass, entry)
    assert result is True
    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        options={
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_MIN_DIM_DURATION: DEFAULT_MIN_DIM_DURATION,
            CONF_MAX_DIM_DURATION: DEFAULT_MAX_DIM_DURATION,
            CONF_FORCE_UPDATE: False,
        },
        version=2,
        minor_version=1,
    )


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
    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        options={
            CONF_LOCAL_ADDRESS: "192.168.1.1",
            CONF_SCAN_INTERVAL: 30,
            CONF_INTERPOLATION_FREQUENCY: 3,
            CONF_MIN_DIM_DURATION: 100,
            CONF_MAX_DIM_DURATION: 1500,
            CONF_FORCE_UPDATE: False,
        },
        version=3,
        minor_version=1,
    )


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_runtime_data_config_not_none(
    mock_api_connector_class, mock_config_entry
):
    """Mutmut: runtime_data = OnyxData(config=onyx_config) -> config=None."""
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="UTC")
    mock_api.events = MagicMock()
    mock_api_connector_class.return_value = mock_api
    hass.async_create_background_task.return_value = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    await async_setup_entry(hass, mock_config_entry)

    assert mock_config_entry.runtime_data.config is not None


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_event_task_uses_events_not_none(
    mock_api_connector_class, mock_config_entry
):
    """Mutmut: async_create_background_task(onyx_api.events(...)) -> (None, ...)."""
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="UTC")
    mock_api_connector_class.return_value = mock_api
    hass.async_create_background_task.return_value = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    await async_setup_entry(hass, mock_config_entry)

    call_args = hass.async_create_background_task.call_args
    # First positional arg must not be None
    assert call_args[0][0] is not None


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_scan_interval_key_used(
    mock_api_connector_class, mock_config_entry
):
    """Mutmut: entry.options.get(CONF_SCAN_INTERVAL, ...) -> .get(None, ...)."""
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="UTC")
    mock_api_connector_class.return_value = mock_api
    hass.async_create_background_task.return_value = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    await async_setup_entry(hass, mock_config_entry)

    _, call_kwargs = mock_api_connector_class.call_args
    config = mock_api_connector_class.call_args[0][1]
    # scan_interval must reflect the value from the config entry, not the default
    assert config.scan_interval == 120


@pytest.mark.asyncio
async def test_async_migrate_entry_v2_defaults():
    hass = MagicMock()
    entry = ConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        source="user",
        unique_id="test",
        options={},
        discovery_keys={},
        subentries_data={},
    )
    result = await async_migrate_entry(hass, entry)
    assert result is True
    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
        },
        options={
            CONF_LOCAL_ADDRESS: None,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_INTERPOLATION_FREQUENCY: DEFAULT_INTERPOLATION_FREQUENCY,
            CONF_MIN_DIM_DURATION: DEFAULT_MIN_DIM_DURATION,
            CONF_MAX_DIM_DURATION: DEFAULT_MAX_DIM_DURATION,
            CONF_FORCE_UPDATE: False,
        },
        version=3,
        minor_version=1,
    )


@pytest.mark.asyncio
async def test_async_migrate_entry_v2_force_update_key_used():
    """Mutmut: old_data.get(CONF_FORCE_UPDATE, False) -> old_data.get(None, False).

    When old_data contains CONF_FORCE_UPDATE=True the real key must be used so
    the value survives migration; using None as key returns the default (False).
    """
    hass = MagicMock()
    entry = ConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fingerprint_123",
            CONF_ACCESS_TOKEN: "token_123",
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
    call_kwargs = hass.config_entries.async_update_entry.call_args[1]
    assert call_kwargs["options"][CONF_FORCE_UPDATE] is True


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_options_fallbacks(
    mock_api_connector_class,
):
    """Verify options fallbacks when empty dict is provided."""
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="UTC")
    mock_api_connector_class.return_value = mock_api
    hass.async_create_background_task.return_value = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    entry = ConfigEntry(
        version=3,
        minor_version=1,
        domain=DOMAIN,
        title="test_fingerprint",
        data={
            CONF_FINGERPRINT: "fp",
            CONF_ACCESS_TOKEN: "tok",
        },
        source="user",
        unique_id="fp",
        options={},
        discovery_keys={},
        subentries_data={},
    )

    await async_setup_entry(hass, entry)

    config = mock_api_connector_class.call_args[0][1]
    assert config.local_address is None
    assert config.scan_interval == DEFAULT_SCAN_INTERVAL
    assert config.interpolation_frequency == DEFAULT_INTERPOLATION_FREQUENCY
    assert config.additional_delay == DEFAULT_ADDITIONAL_DELAY
    assert config.min_dim_duration == DEFAULT_MIN_DIM_DURATION
    assert config.max_dim_duration == DEFAULT_MAX_DIM_DURATION
    assert config.force_update is False

    task_call_kwargs = hass.async_create_background_task.call_args[1]
    assert task_call_kwargs["name"] == f"{DOMAIN}_{entry.entry_id}_events"
    hass.config_entries.async_forward_entry_setups.assert_called_once_with(
        entry, PLATFORMS
    )


@pytest.mark.asyncio
@patch("custom_components.hella_onyx.APIConnector")
async def test_async_setup_entry_custom_option_keys(
    mock_api_connector_class,
):
    """Verify custom option keys are properly extracted from options."""
    hass = MagicMock()
    hass.data = {}
    mock_api = MagicMock()
    mock_api.async_config_entry_first_refresh = AsyncMock()
    mock_api.get_timezone = AsyncMock(return_value="UTC")
    mock_api_connector_class.return_value = mock_api
    hass.async_create_background_task.return_value = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    entry = ConfigEntry(
        version=3,
        minor_version=1,
        domain=DOMAIN,
        title="test_fingerprint",
        data={
            CONF_FINGERPRINT: "fp",
            CONF_ACCESS_TOKEN: "tok",
        },
        source="user",
        unique_id="fp",
        options={
            CONF_INTERPOLATION_FREQUENCY: 99,
            CONF_ADDITIONAL_DELAY: 888,
            CONF_MIN_DIM_DURATION: 77,
            CONF_MAX_DIM_DURATION: 666,
            CONF_FORCE_UPDATE: True,
        },
        discovery_keys={},
        subentries_data={},
    )

    await async_setup_entry(hass, entry)

    config = mock_api_connector_class.call_args[0][1]
    assert config.interpolation_frequency == 99
    assert config.additional_delay == 888
    assert config.min_dim_duration == 77
    assert config.max_dim_duration == 666
    assert config.force_update is True


@pytest.mark.asyncio
async def test_async_migrate_entry_v1_keys_and_defaults():
    hass = MagicMock()
    entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fp_v1",
            CONF_ACCESS_TOKEN: "tok_v1",
            CONF_SCAN_INTERVAL: 42,
            CONF_MIN_DIM_DURATION: 123,
            CONF_MAX_DIM_DURATION: 456,
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
    call_kwargs = hass.config_entries.async_update_entry.call_args[1]
    assert call_kwargs["options"][CONF_SCAN_INTERVAL] == 42
    assert call_kwargs["options"][CONF_MIN_DIM_DURATION] == 123
    assert call_kwargs["options"][CONF_MAX_DIM_DURATION] == 456
    assert call_kwargs["options"][CONF_FORCE_UPDATE] is True


@pytest.mark.asyncio
async def test_async_migrate_entry_v2_keys():
    hass = MagicMock()
    entry = ConfigEntry(
        version=2,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={
            CONF_FINGERPRINT: "fp_v2",
            CONF_ACCESS_TOKEN: "tok_v2",
            CONF_LOCAL_ADDRESS: "10.0.0.99",
            CONF_SCAN_INTERVAL: 42,
            CONF_INTERPOLATION_FREQUENCY: 7,
            CONF_MIN_DIM_DURATION: 123,
            CONF_MAX_DIM_DURATION: 456,
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
    call_kwargs = hass.config_entries.async_update_entry.call_args[1]
    assert call_kwargs["options"][CONF_LOCAL_ADDRESS] == "10.0.0.99"
    assert call_kwargs["options"][CONF_SCAN_INTERVAL] == 42
    assert call_kwargs["options"][CONF_INTERPOLATION_FREQUENCY] == 7
    assert call_kwargs["options"][CONF_MIN_DIM_DURATION] == 123
    assert call_kwargs["options"][CONF_MAX_DIM_DURATION] == 456
    assert call_kwargs["options"][CONF_FORCE_UPDATE] is True
