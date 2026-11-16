"""Expose all UniFi Policy Engine rules as switches.

Docks onto the hub of a loaded UniFi Network config entry instead of opening
an own connection, and only adds rules the UniFi integration doesn't cover.
"""

from homeassistant.components.unifi.hub import UnifiHub
from homeassistant.config_entries import (
    SIGNAL_CONFIG_ENTRY_CHANGED,
    ConfigEntry,
    ConfigEntryChange,
    ConfigEntryState,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import ConfigType

from .const import CONF_UNIFI_ENTRY_ID, DOMAIN, PLATFORMS, UNIFI_DOMAIN

type UnifiPolicySwitchesConfigEntry = ConfigEntry[UnifiHub]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Follow the state of the UniFi config entries."""

    @callback
    def async_unifi_entry_changed(
        change: ConfigEntryChange, unifi_entry: ConfigEntry
    ) -> None:
        """Reload entries using a UniFi entry that was reloaded or unloaded."""
        if unifi_entry.domain != UNIFI_DOMAIN:
            return
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.data[CONF_UNIFI_ENTRY_ID] == unifi_entry.entry_id and (
                _async_needs_reload(entry, change, unifi_entry)
            ):
                hass.config_entries.async_schedule_reload(entry.entry_id)

    async_dispatcher_connect(
        hass, SIGNAL_CONFIG_ENTRY_CHANGED, async_unifi_entry_changed
    )
    return True


@callback
def _async_needs_reload(
    entry: UnifiPolicySwitchesConfigEntry,
    change: ConfigEntryChange,
    unifi_entry: ConfigEntry[UnifiHub],
) -> bool:
    """Return if the entry has to follow a change of its UniFi entry."""
    unifi_loaded = (
        change is not ConfigEntryChange.REMOVED
        and unifi_entry.state is ConfigEntryState.LOADED
    )
    if entry.state is ConfigEntryState.LOADED:
        # A reloaded UniFi entry has a new hub, the old one is stopped
        return not unifi_loaded or unifi_entry.runtime_data is not entry.runtime_data
    # Don't wait for the retry backoff once the UniFi entry is back
    return entry.state is ConfigEntryState.SETUP_RETRY and (
        unifi_loaded or change is ConfigEntryChange.REMOVED
    )


async def async_setup_entry(
    hass: HomeAssistant, config_entry: UnifiPolicySwitchesConfigEntry
) -> bool:
    """Set up switches on top of a loaded UniFi Network entry.

    Returns a boolean, Home Assistant before 2026.11 doesn't accept None.
    """
    unifi_entry: ConfigEntry[UnifiHub] | None = hass.config_entries.async_get_entry(
        config_entry.data[CONF_UNIFI_ENTRY_ID]
    )
    if unifi_entry is None or unifi_entry.domain != UNIFI_DOMAIN:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="unifi_entry_missing",
        )
    if unifi_entry.state is not ConfigEntryState.LOADED:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="unifi_entry_not_loaded",
            translation_placeholders={"title": unifi_entry.title},
        )

    config_entry.runtime_data = unifi_entry.runtime_data
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: UnifiPolicySwitchesConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
