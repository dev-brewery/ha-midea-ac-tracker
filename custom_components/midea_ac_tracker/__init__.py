"""Keep Midea Smart AC entries pointed at their unit's current IP address.

Midea Smart AC connects to the fixed host stored in its config entry. Each
entry here links one of those entries to the unit's device_tracker; whenever
the tracker reports a different IP, the Midea entry's host is updated and the
entry reloaded.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_DEVICE_TRACKER, CONF_MIDEA_ENTRY, MIDEA_DOMAIN
from .tracker import tracker_ip

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    midea_entry_id = entry.data[CONF_MIDEA_ENTRY]
    tracker = entry.data[CONF_DEVICE_TRACKER]

    midea = hass.config_entries.async_get_entry(midea_entry_id)
    if midea is None or midea.domain != MIDEA_DOMAIN:
        raise ConfigEntryError(
            f"Midea Smart AC entry {midea_entry_id} no longer exists; "
            "remove this link and add it again for the new entry"
        )

    @callback
    def follow(_event: Event[EventStateChangedData] | None = None) -> None:
        async_follow(hass, midea_entry_id, tracker)

    # Catch up on a move that happened while Home Assistant was down, then
    # follow every later one.
    follow()
    entry.async_on_unload(async_track_state_change_event(hass, [tracker], follow))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


@callback
def async_follow(hass: HomeAssistant, midea_entry_id: str, tracker: str) -> None:
    """Point the Midea entry at the tracker's IP if it moved."""
    midea = hass.config_entries.async_get_entry(midea_entry_id)
    if midea is None:
        _LOGGER.warning("Midea Smart AC entry %s no longer exists", midea_entry_id)
        return
    # No IP means the unit is off the network; keep the last known address.
    if not (ip := tracker_ip(hass, tracker)) or ip == midea.data.get(CONF_HOST):
        return

    _LOGGER.info(
        "%s moved from %s to %s; updating %s",
        tracker,
        midea.data.get(CONF_HOST),
        ip,
        midea.title,
    )
    hass.config_entries.async_update_entry(midea, data={**midea.data, CONF_HOST: ip})
    hass.config_entries.async_schedule_reload(midea.entry_id)
