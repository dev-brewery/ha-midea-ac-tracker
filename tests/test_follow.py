"""Following tests: the Midea entry's host tracks the unit's current IP."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .conftest import HOST, add_midea_entry, set_tracker, setup_link


async def test_follows_the_unit_to_a_new_address(
    hass: HomeAssistant, reloads
) -> None:
    midea = add_midea_entry(hass)
    link = await setup_link(hass, midea)
    assert link.state is ConfigEntryState.LOADED
    reloads.assert_not_called()

    # DHCP hands the unit a new address; the router tracker follows it.
    set_tracker(hass, ip="192.0.2.99")
    await hass.async_block_till_done()

    assert midea.data[CONF_HOST] == "192.0.2.99"
    reloads.assert_called_once_with(midea.entry_id)
    # Everything else the Midea entry needs is untouched.
    assert midea.data["token"] == "00" * 64
    assert midea.data["id"] == 148434069757337


async def test_catches_up_on_a_move_while_ha_was_down(
    hass: HomeAssistant, reloads
) -> None:
    midea = add_midea_entry(hass, host="192.0.2.50")
    await setup_link(hass, midea)

    assert midea.data[CONF_HOST] == HOST
    reloads.assert_called_once_with(midea.entry_id)


async def test_other_attribute_changes_do_not_reload(
    hass: HomeAssistant, reloads
) -> None:
    midea = add_midea_entry(hass)
    await setup_link(hass, midea)

    set_tracker(hass, name="Living Room AC")
    await hass.async_block_till_done()

    reloads.assert_not_called()


async def test_unit_off_the_network_keeps_last_address(
    hass: HomeAssistant, reloads
) -> None:
    midea = add_midea_entry(hass)
    await setup_link(hass, midea)

    set_tracker(hass, ip=None)
    await hass.async_block_till_done()

    assert midea.data[CONF_HOST] == HOST
    reloads.assert_not_called()

    # Back on the network at a new address.
    set_tracker(hass, ip="192.0.2.80")
    await hass.async_block_till_done()
    assert midea.data[CONF_HOST] == "192.0.2.80"
    reloads.assert_called_once_with(midea.entry_id)


async def test_tracker_appearing_after_startup(
    hass: HomeAssistant, reloads
) -> None:
    """The router integration may load after us; its first state still counts."""
    hass.states.async_remove("device_tracker.net_ac_eb32")
    midea = add_midea_entry(hass, host="192.0.2.50")
    link = await setup_link(hass, midea)
    assert link.state is ConfigEntryState.LOADED
    reloads.assert_not_called()

    set_tracker(hass)
    await hass.async_block_till_done()
    assert midea.data[CONF_HOST] == HOST
    reloads.assert_called_once_with(midea.entry_id)


async def test_unloaded_link_stops_following(hass: HomeAssistant, reloads) -> None:
    midea = add_midea_entry(hass)
    link = await setup_link(hass, midea)
    assert await hass.config_entries.async_unload(link.entry_id)

    set_tracker(hass, ip="192.0.2.99")
    await hass.async_block_till_done()

    assert midea.data[CONF_HOST] == HOST
    reloads.assert_not_called()


async def test_two_units_follow_independently(hass: HomeAssistant, reloads) -> None:
    living = add_midea_entry(hass)
    bedroom = add_midea_entry(hass, host="192.0.2.78", device_id="150633093276186")
    set_tracker(
        hass,
        "device_tracker.net_ac_50de",
        ip="192.0.2.78",
        mac="C4-39-60-5F-50-DE",
        name="net_ac_50DE",
    )
    await setup_link(hass, living)
    await setup_link(
        hass,
        bedroom,
        tracker="device_tracker.net_ac_50de",
        unique_id="c4:39:60:5f:50:de",
    )

    set_tracker(
        hass,
        "device_tracker.net_ac_50de",
        ip="192.0.2.88",
        mac="C4-39-60-5F-50-DE",
        name="net_ac_50DE",
    )
    await hass.async_block_till_done()

    assert bedroom.data[CONF_HOST] == "192.0.2.88"
    assert living.data[CONF_HOST] == HOST
    reloads.assert_called_once_with(bedroom.entry_id)


async def test_missing_midea_entry_fails_setup(hass: HomeAssistant, reloads) -> None:
    midea = add_midea_entry(hass)
    await hass.config_entries.async_remove(midea.entry_id)

    link = await setup_link(hass, midea)

    assert link.state is ConfigEntryState.SETUP_ERROR
