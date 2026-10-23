"""Read a unit's identity and address from its device_tracker.

Router integrations (Omada, UniFi, ...) report each Wi-Fi client's current
`ip` and its `mac`. The MAC is the unit's stable identity; the IP is whatever
DHCP handed out last.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac


def tracker_ip(hass: HomeAssistant, entity_id: str) -> str | None:
    state = hass.states.get(entity_id)
    return state.attributes.get("ip") if state else None


def tracker_mac(hass: HomeAssistant, entity_id: str) -> str | None:
    state = hass.states.get(entity_id)
    mac = state.attributes.get("mac") if state else None
    return format_mac(mac) if mac else None


def tracker_name(hass: HomeAssistant, entity_id: str) -> str | None:
    state = hass.states.get(entity_id)
    return state.name if state else None
