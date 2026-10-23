"""Config flow tests."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.midea_ac_tracker.const import (
    CONF_DEVICE_TRACKER,
    CONF_MIDEA_ENTRY,
    DOMAIN,
)

from .conftest import MAC, TRACKER, add_midea_entry, set_tracker, setup_link


async def _submit(hass: HomeAssistant, data):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(result["flow_id"], data)


async def test_links_unit_by_tracker_mac(hass: HomeAssistant, reloads) -> None:
    midea = add_midea_entry(hass)
    result = await _submit(
        hass, {CONF_MIDEA_ENTRY: midea.entry_id, CONF_DEVICE_TRACKER: TRACKER}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "net_ac_EB32"  # the tracker's name
    assert result["result"].unique_id == MAC
    assert result["data"] == {
        CONF_MIDEA_ENTRY: midea.entry_id,
        CONF_DEVICE_TRACKER: TRACKER,
    }


async def test_aborts_without_midea_entries(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_midea_entries"


async def test_tracker_without_mac(hass: HomeAssistant) -> None:
    midea = add_midea_entry(hass)
    set_tracker(hass, mac=None)
    result = await _submit(
        hass, {CONF_MIDEA_ENTRY: midea.entry_id, CONF_DEVICE_TRACKER: TRACKER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_mac"}


async def test_same_unit_cannot_be_linked_twice(hass: HomeAssistant, reloads) -> None:
    midea = add_midea_entry(hass)
    other = add_midea_entry(hass, host="192.0.2.78", device_id="150633093276186")
    await setup_link(hass, midea)

    # Same tracker (MAC) to another Midea entry.
    result = await _submit(
        hass, {CONF_MIDEA_ENTRY: other.entry_id, CONF_DEVICE_TRACKER: TRACKER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    # Same Midea entry to another tracker.
    set_tracker(hass, "device_tracker.other", mac="AA-BB-CC-DD-EE-FF", name="other")
    result = await _submit(
        hass,
        {CONF_MIDEA_ENTRY: midea.entry_id, CONF_DEVICE_TRACKER: "device_tracker.other"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
