"""Fixtures for midea_ac_tracker tests. Midea Smart AC itself is never loaded."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.midea_ac_tracker.const import (
    CONF_DEVICE_TRACKER,
    CONF_MIDEA_ENTRY,
    DOMAIN,
    MIDEA_DOMAIN,
)

TRACKER = "device_tracker.net_ac_eb32"
MAC_RAW = "C4-39-60-5E-EB-32"  # as the router tracker reports it
MAC = "c4:39:60:5e:eb:32"
HOST = "192.0.2.74"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
async def unit_tracker(hass: HomeAssistant) -> None:
    """The unit's router device_tracker, home with an IP and MAC."""
    set_tracker(hass)


@pytest.fixture
def reloads(hass: HomeAssistant):
    """Record Midea entry reloads instead of loading Midea Smart AC."""
    with patch.object(hass.config_entries, "async_schedule_reload") as mock:
        yield mock


def set_tracker(
    hass: HomeAssistant,
    entity_id: str = TRACKER,
    *,
    ip: str | None = HOST,
    mac: str | None = MAC_RAW,
    name: str = "net_ac_EB32",
) -> None:
    attrs: dict[str, Any] = {"friendly_name": name, "source_type": "router"}
    if ip:
        attrs["ip"] = ip
    if mac:
        attrs["mac"] = mac
    hass.states.async_set(entity_id, "home" if ip else "not_home", attrs)


def add_midea_entry(
    hass: HomeAssistant, *, host: str = HOST, device_id: str = "148434069757337"
) -> MockConfigEntry:
    """A Midea Smart AC entry as its manual config flow creates it."""
    entry = MockConfigEntry(
        domain=MIDEA_DOMAIN,
        title=f"midea_ac {device_id}",
        unique_id=device_id,
        data={
            "device_type": 0xAC,
            "id": int(device_id),
            CONF_HOST: host,
            "port": 6444,
            "token": "00" * 64,
            "k1": "00" * 32,
        },
    )
    entry.add_to_hass(hass)
    return entry


async def setup_link(
    hass: HomeAssistant,
    midea: MockConfigEntry,
    *,
    tracker: str = TRACKER,
    unique_id: str = MAC,
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="net_ac_EB32",
        unique_id=unique_id,
        data={CONF_MIDEA_ENTRY: midea.entry_id, CONF_DEVICE_TRACKER: tracker},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
