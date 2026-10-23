"""Config flow: link a Midea Smart AC entry to the unit's device_tracker.

The tracker's MAC is the link's unique ID, so a unit can only be linked once,
and each Midea entry can only follow one tracker.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector

from .const import CONF_DEVICE_TRACKER, CONF_MIDEA_ENTRY, DOMAIN, MIDEA_DOMAIN
from .tracker import tracker_mac, tracker_name


def midea_label(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """The unit's device name if it has one, else the entry title."""
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    for device in devices:
        if name := device.name_by_user or device.name:
            return f"{name} ({entry.title})"
    return entry.title


class MideaAcTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick a Midea Smart AC entry and the tracker that follows the same unit."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        midea_entries = self.hass.config_entries.async_entries(MIDEA_DOMAIN)
        if not midea_entries:
            return self.async_abort(reason="no_midea_entries")

        if user_input is not None:
            tracker = user_input[CONF_DEVICE_TRACKER]
            midea = self.hass.config_entries.async_get_entry(
                user_input[CONF_MIDEA_ENTRY]
            )
            if midea is None or midea.domain != MIDEA_DOMAIN:
                errors["base"] = "unknown_midea_entry"
            elif (mac := tracker_mac(self.hass, tracker)) is None:
                errors["base"] = "no_mac"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()
                self._async_abort_entries_match({CONF_MIDEA_ENTRY: midea.entry_id})
                return self.async_create_entry(
                    title=tracker_name(self.hass, tracker) or midea.title,
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_MIDEA_ENTRY): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=entry.entry_id,
                                label=midea_label(self.hass, entry),
                            )
                            for entry in midea_entries
                        ]
                    )
                ),
                vol.Required(CONF_DEVICE_TRACKER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
