"""Import the integration and check the rule filter without pytest plugins.

For Home Assistant versions without a matching
pytest-homeassistant-custom-component release. All rule data is synthetic.
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock

# Home Assistant has to be imported first, it aliases httpx on import
import homeassistant  # noqa: F401  isort:skip

from aiounifi.interfaces.object_oriented_network_configs import (
    ObjectOrientedNetworkConfigs,
)

from homeassistant.const import __version__ as HA_VERSION

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.unifi_policy_switches import (  # noqa: E402
    config_flow,  # noqa: F401
)
from custom_components.unifi_policy_switches.switch import (  # noqa: E402
    async_policy_switch_supported_fn,
)

RULES = [
    {
        "_id": "core",
        "name": "Synthetic bedtime block",
        "enabled": True,
        "secure": {"enabled": True, "internet": {"mode": "TURN_OFF_INTERNET"}},
    },
    {"_id": "qos", "name": "Synthetic guest QoS", "enabled": True},
    {
        "id": "secure_off",
        "name": "Synthetic route rule",
        "enabled": False,
        "secure": {"enabled": False, "internet": {"mode": "TURN_OFF_INTERNET"}},
    },
    {"_id": "empty_name", "name": "", "enabled": True},
    {"_id": "no_name", "enabled": True},
]
EXPECTED = {
    "core": False,
    "qos": True,
    "secure_off": True,
    "empty_name": False,
    "no_name": False,
    "unknown": False,
}


def main() -> int:
    """Run the smoke test."""
    handler = ObjectOrientedNetworkConfigs(MagicMock())
    handler.process_raw(RULES)
    hub = MagicMock()
    hub.api.object_oriented_network_configs = handler

    result = {
        obj_id: async_policy_switch_supported_fn(hub, obj_id) for obj_id in EXPECTED
    }
    if result != EXPECTED:
        print(f"FAILED on Home Assistant {HA_VERSION}: {result} != {EXPECTED}")
        return 1
    print(f"Smoke test passed on Home Assistant {HA_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
