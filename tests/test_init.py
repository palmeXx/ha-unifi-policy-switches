"""Tests for setup and the coupling to the UniFi Network entry."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import FakeUnifiHub
from .test_switch import QOS_ENTITY_ID


async def test_setup_waits_for_unifi_entry(
    hass: HomeAssistant,
    unifi_entry: MockConfigEntry,
    hub: FakeUnifiHub,
    config_entry: MockConfigEntry,
) -> None:
    """Setup is retried until the UniFi entry is loaded, then follows at once."""
    unifi_entry.mock_state(hass, ConfigEntryState.SETUP_RETRY)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert "Synthetic UniFi site" in config_entry.reason

    unifi_entry.mock_state(hass, ConfigEntryState.LOADED)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.runtime_data is hub
    assert hass.states.get(QOS_ENTITY_ID) is not None


async def test_setup_unifi_entry_missing(
    hass: HomeAssistant, config_entry: MockConfigEntry, unifi_entry: MockConfigEntry
) -> None:
    """Setup fails for good without the UniFi entry."""
    await hass.config_entries.async_remove(unifi_entry.entry_id)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_follows_unifi_reload(
    hass: HomeAssistant,
    unifi_entry: MockConfigEntry,
    hub: FakeUnifiHub,
    setup_integration: MockConfigEntry,
) -> None:
    """Unloading and reloading the UniFi entry moves to the new hub."""
    unifi_entry.mock_state(hass, ConfigEntryState.NOT_LOADED)
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.SETUP_RETRY
    assert hass.states.get(QOS_ENTITY_ID).state == "unavailable"

    new_hub = FakeUnifiHub(unifi_entry)
    new_hub.api.object_oriented_network_configs.process_raw(
        [r.raw for r in hub.api.object_oriented_network_configs.values()]
    )
    unifi_entry.runtime_data = new_hub
    unifi_entry.mock_state(hass, ConfigEntryState.LOADED)
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.LOADED
    assert setup_integration.runtime_data is new_hub
    assert hass.states.get(QOS_ENTITY_ID).state == "on"


async def test_unrelated_entry_updates_dont_reload(
    hass: HomeAssistant,
    unifi_entry: MockConfigEntry,
    hub: FakeUnifiHub,
    setup_integration: MockConfigEntry,
) -> None:
    """Updates of the loaded UniFi entry with the same hub keep the entry."""
    hass.config_entries.async_update_entry(unifi_entry, options={"track_clients": False})
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.LOADED
    assert setup_integration.runtime_data is hub


@pytest.mark.usefixtures("hub")
async def test_unload(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Entry can be unloaded."""
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.NOT_LOADED
