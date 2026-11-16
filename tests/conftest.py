"""Fixtures for UniFi Policy Engine switches tests.

All rule data is synthetic. The UniFi hub is replaced by a small fake carrying
a real aiounifi handler, so tests run against aiounifi without a controller.
"""

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from aiounifi.interfaces.object_oriented_network_configs import (
    ObjectOrientedNetworkConfigs,
)
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_component,
)

from custom_components.unifi_policy_switches.const import (
    CONF_UNIFI_ENTRY_ID,
    DOMAIN,
    UNIFI_DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

# Synthetic site and rule IDs, not taken from a real controller
UNIFI_UNIQUE_ID = "00000000-0000-4000-8000-000000000001"

# Handled by the UniFi integration: blocks internet access
RULE_CORE = {
    "_id": "000000000000000000000c01",
    "name": "Synthetic bedtime block",
    "enabled": True,
    "target_type": "CLIENTS",
    "targets": [],
    "secure": {"enabled": True, "internet": {"mode": "TURN_OFF_INTERNET"}},
}
# QoS only rule
RULE_QOS = {
    "_id": "000000000000000000000a01",
    "name": "Synthetic guest QoS",
    "enabled": True,
    "qos": {"enabled": True},
}
# Internet block exists but the secure part is off
RULE_SECURE_OFF = {
    "id": "000000000000000000000a02",
    "name": "Synthetic route rule",
    "enabled": False,
    "route": {"enabled": True},
    "secure": {"enabled": False, "internet": {"mode": "TURN_OFF_INTERNET"}},
}
RULE_NO_NAME = {
    "_id": "000000000000000000000a03",
    "name": "",
    "enabled": True,
}


class FakeUnifiHub:
    """The parts of UnifiHub used by the integration."""

    def __init__(self, unifi_entry: MockConfigEntry) -> None:
        """Set up fake hub."""
        self.controller = MagicMock()
        self.controller.request = AsyncMock()
        self.api = MagicMock()
        self.api.object_oriented_network_configs = ObjectOrientedNetworkConfigs(
            self.controller
        )
        self.config = MagicMock(entry=unifi_entry)
        self.available = True
        self.is_admin = True

    @property
    def signal_reachable(self) -> str:
        """Same signal as UnifiHub."""
        return f"unifi-reachable-{self.config.entry.entry_id}"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations."""


@pytest.fixture(autouse=True)
def mock_unifi_component(hass: HomeAssistant) -> None:
    """Mock the UniFi integration as set up, it would start discovery."""
    mock_component(hass, UNIFI_DOMAIN)


@pytest.fixture
def rules() -> list[dict[str, Any]]:
    """Rules known to the hub on setup."""
    return deepcopy([RULE_CORE, RULE_QOS, RULE_SECURE_OFF, RULE_NO_NAME])


@pytest.fixture
def unifi_entry(hass: HomeAssistant) -> MockConfigEntry:
    """UniFi Network entry, loaded once the hub fixture is used."""
    entry = MockConfigEntry(
        domain=UNIFI_DOMAIN,
        unique_id=UNIFI_UNIQUE_ID,
        title="Synthetic UniFi site",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def hub(
    hass: HomeAssistant, unifi_entry: MockConfigEntry, rules: list[dict[str, Any]]
) -> FakeUnifiHub:
    """Hub of the loaded UniFi entry."""
    hub = FakeUnifiHub(unifi_entry)
    hub.api.object_oriented_network_configs.process_raw(rules)
    unifi_entry.runtime_data = hub
    unifi_entry.mock_state(hass, ConfigEntryState.LOADED)
    return hub


@pytest.fixture
def config_entry(hass: HomeAssistant, unifi_entry: MockConfigEntry) -> MockConfigEntry:
    """Entry of this integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=unifi_entry.entry_id,
        title=unifi_entry.title,
        data={CONF_UNIFI_ENTRY_ID: unifi_entry.entry_id},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, hub: FakeUnifiHub, config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the integration on a loaded UniFi entry."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
