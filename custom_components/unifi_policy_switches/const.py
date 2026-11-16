"""Constants for the UniFi Policy Engine switches integration."""

from homeassistant.const import Platform

DOMAIN = "unifi_policy_switches"
UNIFI_DOMAIN = "unifi"

CONF_UNIFI_ENTRY_ID = "unifi_entry_id"

PLATFORMS = [Platform.SWITCH]

UNIQUE_ID_PREFIX = "policy_switch"
