"""Check the UniFi core internals this integration relies on.

The tests run against a fake hub, these checks fail first when an update of
Home Assistant or aiounifi changes what the fake stands in for.
"""

import inspect

from aiounifi.controller import Controller
from aiounifi.interfaces.object_oriented_network_configs import (
    ObjectOrientedNetworkConfigs,
)
from aiounifi.models.object_oriented_network_config import ObjectOrientedNetworkConfig

from homeassistant.components.unifi import switch as unifi_switch
from homeassistant.components.unifi.hub import UnifiHub

from .conftest import RULE_CORE, RULE_QOS, RULE_SECURE_OFF, FakeUnifiHub


def test_hub_interface() -> None:
    """The fake hub provides what UnifiHub provides."""
    assert isinstance(UnifiHub.available, property)
    assert isinstance(UnifiHub.signal_reachable, property)
    init_source = inspect.getsource(UnifiHub.__init__)
    for attribute in ("self.api =", "self.config =", "self.is_admin ="):
        assert attribute in init_source
    assert set(inspect.signature(FakeUnifiHub.__init__).parameters) <= {
        "self",
        "unifi_entry",
    }


def test_aiounifi_handler() -> None:
    """Policy Engine rules are a handler of the aiounifi controller."""
    assert "object_oriented_network_configs" in inspect.getsource(Controller.__init__)
    assert "id_filter" in inspect.signature(ObjectOrientedNetworkConfigs.subscribe).parameters
    assert "state" in inspect.signature(ObjectOrientedNetworkConfigs.save).parameters


def test_core_supported_rules(hub: FakeUnifiHub) -> None:
    """The core switch platform only handles enabled internet blocks."""
    for rule, supported in (
        (RULE_CORE, True),
        (RULE_QOS, False),
        (RULE_SECURE_OFF, False),
    ):
        obj_id = ObjectOrientedNetworkConfig(rule).id
        assert (
            unifi_switch.async_object_oriented_network_config_supported_fn(hub, obj_id)
            is supported
        )
