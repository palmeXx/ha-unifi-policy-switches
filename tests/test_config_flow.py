"""Tests for the config flow."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_policy_switches.const import CONF_UNIFI_ENTRY_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_user_flow(hass: HomeAssistant, unifi_entry: MockConfigEntry) -> None:
    """The user picks the UniFi entry to use."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UNIFI_ENTRY_ID: unifi_entry.entry_id}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Synthetic UniFi site"
    assert result["data"] == {CONF_UNIFI_ENTRY_ID: unifi_entry.entry_id}
    assert result["result"].unique_id == unifi_entry.entry_id


async def test_no_unifi_entries(hass: HomeAssistant) -> None:
    """The flow aborts without a UniFi entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_unifi_entries"


async def test_unifi_entry_already_used(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A UniFi entry can only be used once."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_unifi_entries"
