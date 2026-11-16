"""Tests for UniFi Policy Engine switches."""

from copy import deepcopy

import aiounifi
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .conftest import (
    RULE_CORE,
    RULE_NO_NAME,
    RULE_QOS,
    RULE_SECURE_OFF,
    UNIFI_UNIQUE_ID,
    FakeUnifiHub,
)

QOS_ENTITY_ID = "switch.unifi_network_synthetic_guest_qos"
SECURE_OFF_ENTITY_ID = "switch.unifi_network_synthetic_route_rule"


def _unique_ids(hass: HomeAssistant, config_entry: MockConfigEntry) -> set[str]:
    return {
        entry.unique_id
        for entry in er.async_entries_for_config_entry(
            er.async_get(hass), config_entry.entry_id
        )
    }


@pytest.mark.usefixtures("setup_integration")
async def test_switches_for_rules_not_covered_by_core(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
) -> None:
    """Only named rules the UniFi integration doesn't handle get a switch."""
    assert config_entry.state is ConfigEntryState.LOADED
    assert _unique_ids(hass, config_entry) == {
        f"policy_switch-{RULE_QOS['_id']}",
        f"policy_switch-{RULE_SECURE_OFF['id']}",
    }

    assert hass.states.get(QOS_ENTITY_ID).state == STATE_ON
    assert hass.states.get(SECURE_OFF_ENTITY_ID).state == STATE_OFF

    entry = entity_registry.async_get(QOS_ENTITY_ID)
    assert entry.entity_category is EntityCategory.CONFIG
    # Shares the device of the UniFi Policy Engine switches
    device = device_registry.async_get(entry.device_id)
    assert device.identifiers == {(SWITCH_DOMAIN, UNIFI_UNIQUE_ID)}


@pytest.mark.usefixtures("setup_integration")
@pytest.mark.parametrize(
    ("service", "expected_enabled", "expected_state"),
    [(SERVICE_TURN_OFF, False, STATE_OFF), (SERVICE_TURN_ON, True, STATE_ON)],
)
async def test_control(
    hass: HomeAssistant,
    hub: FakeUnifiHub,
    service: str,
    expected_enabled: bool,
    expected_state: str,
) -> None:
    """Switching saves the rule, the response updates the state."""
    handler = hub.api.object_oriented_network_configs
    handler.process_raw([RULE_QOS | {"enabled": not expected_enabled}])
    await hass.async_block_till_done()
    assert hass.states.get(QOS_ENTITY_ID).state != expected_state

    response = deepcopy(RULE_QOS) | {"enabled": expected_enabled}
    hub.controller.request.return_value = {"meta": {}, "data": [response]}

    await hass.services.async_call(
        SWITCH_DOMAIN, service, {ATTR_ENTITY_ID: QOS_ENTITY_ID}, blocking=True
    )

    request = hub.controller.request.call_args.args[0]
    assert request.method == "put"
    assert request.path == f"/object-oriented-network-config/{RULE_QOS['_id']}"
    assert request.data == RULE_QOS | {"enabled": expected_enabled}
    assert hass.states.get(QOS_ENTITY_ID).state == expected_state


@pytest.mark.usefixtures("setup_integration")
async def test_control_failed(hass: HomeAssistant, hub: FakeUnifiHub) -> None:
    """A failing request raises a translated error."""
    hub.controller.request.side_effect = aiounifi.AiounifiException

    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: QOS_ENTITY_ID},
            blocking=True,
        )
    assert exc_info.value.translation_key == "action_request_failed"
    assert hass.states.get(QOS_ENTITY_ID).state == STATE_ON


@pytest.mark.usefixtures("setup_integration")
async def test_rule_updates(hass: HomeAssistant, hub: FakeUnifiHub) -> None:
    """Polled rule changes update state and name."""
    handler = hub.api.object_oriented_network_configs
    handler.process_raw(
        [RULE_SECURE_OFF | {"enabled": True, "name": "Synthetic renamed rule"}]
    )
    await hass.async_block_till_done()

    state = hass.states.get(SECURE_OFF_ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes["friendly_name"] == "UniFi Network Synthetic renamed rule"


@pytest.mark.usefixtures("setup_integration")
async def test_rules_added_and_removed(
    hass: HomeAssistant, hub: FakeUnifiHub, config_entry: MockConfigEntry
) -> None:
    """Rules get or lose a switch when they appear, change or are deleted."""
    handler = hub.api.object_oriented_network_configs
    qos_unique_id = f"policy_switch-{RULE_QOS['_id']}"
    new_rule = {
        "_id": "000000000000000000000a04",
        "name": "Synthetic new rule",
        "enabled": False,
    }

    handler.process_raw([new_rule])
    await hass.async_block_till_done()
    assert f"policy_switch-{new_rule['_id']}" in _unique_ids(hass, config_entry)
    assert hass.states.get("switch.unifi_network_synthetic_new_rule").state == STATE_OFF

    # A named rule without a switch yet
    handler.process_raw([RULE_NO_NAME | {"name": "Synthetic named later"}])
    await hass.async_block_till_done()
    assert f"policy_switch-{RULE_NO_NAME['_id']}" in _unique_ids(hass, config_entry)

    # The UniFi integration takes over a rule blocking internet access
    handler.process_raw([RULE_QOS | {"secure": RULE_CORE["secure"]}])
    await hass.async_block_till_done()
    assert qos_unique_id not in _unique_ids(hass, config_entry)
    assert hass.states.get(QOS_ENTITY_ID) is None

    # And hands it back
    handler.process_raw([RULE_QOS])
    await hass.async_block_till_done()
    assert qos_unique_id in _unique_ids(hass, config_entry)
    assert hass.states.get(QOS_ENTITY_ID).state == STATE_ON

    handler.remove_item(RULE_QOS)
    await hass.async_block_till_done()
    assert qos_unique_id not in _unique_ids(hass, config_entry)
    assert hass.states.get(QOS_ENTITY_ID) is None


@pytest.mark.usefixtures("setup_integration")
async def test_core_rule_stays_with_core(
    hass: HomeAssistant, hub: FakeUnifiHub, config_entry: MockConfigEntry
) -> None:
    """Changes of a rule handled by the UniFi integration add no switch."""
    hub.api.object_oriented_network_configs.process_raw(
        [RULE_CORE | {"enabled": False}]
    )
    await hass.async_block_till_done()
    assert f"policy_switch-{RULE_CORE['_id']}" not in _unique_ids(hass, config_entry)


@pytest.mark.usefixtures("setup_integration")
async def test_availability(hass: HomeAssistant, hub: FakeUnifiHub) -> None:
    """Switches follow the UniFi session state."""
    hub.available = False
    async_dispatcher_send(hass, hub.signal_reachable)
    await hass.async_block_till_done()
    assert hass.states.get(QOS_ENTITY_ID).state == STATE_UNAVAILABLE

    hub.available = True
    async_dispatcher_send(hass, hub.signal_reachable)
    await hass.async_block_till_done()
    assert hass.states.get(QOS_ENTITY_ID).state == STATE_ON


async def test_no_switches_without_admin(
    hass: HomeAssistant, hub: FakeUnifiHub, config_entry: MockConfigEntry
) -> None:
    """Like the UniFi switches, rules can only be controlled by admins."""
    hub.is_admin = False
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert not _unique_ids(hass, config_entry)
    hub.api.object_oriented_network_configs.process_raw([RULE_QOS])
    await hass.async_block_till_done()
    assert not _unique_ids(hass, config_entry)


async def test_unload_unsubscribes(
    hass: HomeAssistant, hub: FakeUnifiHub, setup_integration: MockConfigEntry
) -> None:
    """Unloading stops reacting to rule updates."""
    await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.NOT_LOADED

    subscribers = hub.api.object_oriented_network_configs._subscribers
    assert all(not callbacks for callbacks in subscribers.values())
