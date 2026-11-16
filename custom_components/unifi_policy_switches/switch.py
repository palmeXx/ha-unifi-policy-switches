"""Switches for UniFi Policy Engine rules the UniFi integration doesn't cover.

The UniFi integration only adds switches for rules blocking internet access,
see async_object_oriented_network_config_supported_fn. Every other named rule
gets a switch here, rules can move between both while their config changes.
"""

from typing import Any, override

import aiounifi
from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.interfaces.object_oriented_network_configs import (
    ObjectOrientedNetworkConfigs,
)

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.components.unifi.hub import UnifiHub
from homeassistant.components.unifi.switch import (
    async_object_oriented_network_config_supported_fn,
    async_unifi_network_device_info_fn,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import UnifiPolicySwitchesConfigEntry
from .const import DOMAIN, UNIQUE_ID_PREFIX


@callback
def async_policy_switch_supported_fn(hub: UnifiHub, obj_id: str) -> bool:
    """Check if a Policy Engine rule needs a switch of this integration."""
    config = hub.api.object_oriented_network_configs.get(obj_id)
    return (
        config is not None
        and bool(config.raw.get("name"))
        and not async_object_oriented_network_config_supported_fn(hub, obj_id)
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: UnifiPolicySwitchesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches for Policy Engine rules."""
    hub = config_entry.runtime_data
    # Same as the UniFi switch platform, rules can only be changed by admins
    if not hub.is_admin:
        return

    handler = hub.api.object_oriented_network_configs
    known_obj_ids: set[str] = set()

    @callback
    def async_add_switch(event: ItemEvent, obj_id: str) -> None:
        """Add a switch for a new or no longer UniFi controlled rule."""
        if obj_id in known_obj_ids or not async_policy_switch_supported_fn(
            hub, obj_id
        ):
            return
        known_obj_ids.add(obj_id)
        async_add_entities([UnifiPolicySwitchEntity(hub, obj_id, known_obj_ids)])

    for obj_id in list(handler):
        async_add_switch(ItemEvent.ADDED, obj_id)

    config_entry.async_on_unload(
        handler.subscribe(async_add_switch, (ItemEvent.ADDED, ItemEvent.CHANGED))
    )


class UnifiPolicySwitchEntity(SwitchEntity):
    """Switch enabling or disabling a Policy Engine rule."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: UnifiHub, obj_id: str, known_obj_ids: set[str]) -> None:
        """Set up switch entity."""
        self.hub = hub
        self._obj_id = obj_id
        self._known_obj_ids = known_obj_ids
        self._removed = False

        self._attr_unique_id = f"{UNIQUE_ID_PREFIX}-{obj_id}"
        self._attr_device_info = async_unifi_network_device_info_fn(hub, obj_id)
        self._async_update_attrs()

    @property
    def handler(self) -> ObjectOrientedNetworkConfigs:
        """Return the aiounifi handler of Policy Engine rules."""
        return self.hub.api.object_oriented_network_configs

    @property
    @override
    def available(self) -> bool:
        """Return if the UniFi Network session is up."""
        return self.hub.available

    @override
    async def async_added_to_hass(self) -> None:
        """Subscribe to rule and connection updates."""
        self.async_on_remove(
            lambda: self._known_obj_ids.discard(self._obj_id)
        )
        self.async_on_remove(
            self.handler.subscribe(self._async_handle_event, id_filter=self._obj_id)
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.hub.signal_reachable, self.async_write_ha_state
            )
        )

    @callback
    def _async_handle_event(self, event: ItemEvent, obj_id: str) -> None:
        """Update state, or remove the switch if the rule is gone or unsupported."""
        if event is ItemEvent.DELETED or not async_policy_switch_supported_fn(
            self.hub, obj_id
        ):
            self.hass.async_create_task(self._async_remove_switch())
            return
        self._async_update_attrs()
        self.async_write_ha_state()

    @callback
    def _async_update_attrs(self) -> None:
        """Update attributes from the rule."""
        config = self.handler[self._obj_id]
        self._attr_name = config.name
        self._attr_is_on = config.enabled

    async def _async_remove_switch(self) -> None:
        """Remove the switch, also from the entity registry."""
        if self._removed:
            return
        self._removed = True
        if self.registry_entry:
            er.async_get(self.hass).async_remove(self.entity_id)
        else:
            await self.async_remove(force_remove=True)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the rule."""
        await self._async_save(True)

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the rule."""
        await self._async_save(False)

    async def _async_save(self, target: bool) -> None:
        """Save the rule state, the response updates the switch."""
        try:
            await self.handler.save(self.handler[self._obj_id], target)
        except aiounifi.AiounifiException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_request_failed",
            ) from err
