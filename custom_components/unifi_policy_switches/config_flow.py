"""Config flow to pick the UniFi Network entry to dock onto."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import CONF_UNIFI_ENTRY_ID, DOMAIN, UNIFI_DOMAIN


class UnifiPolicySwitchesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Policy Engine switches."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select an UniFi Network entry that isn't used yet."""
        configured = self._async_current_ids(include_ignore=False)
        unifi_entries = {
            entry.entry_id: entry.title
            for entry in self.hass.config_entries.async_entries(UNIFI_DOMAIN)
            if entry.entry_id not in configured
        }

        if user_input is not None:
            unifi_entry_id = user_input[CONF_UNIFI_ENTRY_ID]
            await self.async_set_unique_id(unifi_entry_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=unifi_entries[unifi_entry_id],
                data={CONF_UNIFI_ENTRY_ID: unifi_entry_id},
            )

        if not unifi_entries:
            return self.async_abort(reason="no_unifi_entries")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UNIFI_ENTRY_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=entry_id, label=title)
                                for entry_id, title in unifi_entries.items()
                            ]
                        )
                    )
                }
            ),
        )
