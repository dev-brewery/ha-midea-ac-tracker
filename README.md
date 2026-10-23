# Midea AC Tracker for Home Assistant

Keeps [Midea Smart AC](https://github.com/mill1000/midea-ac-py) units reachable
when DHCP gives them a new IP address.

Midea Smart AC connects to the fixed host stored in each unit's config entry.
When the unit's lease changes, the entry keeps talking to the old address and
the unit goes unavailable. This integration links each unit's Midea Smart AC
entry to the unit's `device_tracker` from a router integration (Omada, UniFi,
...). The tracker's MAC address is the unit's identity. Whenever the tracker
reports a different IP, the Midea entry's host is updated and the entry
reloaded. Its devices, entities, history and automations stay as they are.

Midea Smart AC itself is unchanged, so it keeps updating normally through HACS.

## How it behaves

- On start, and on every tracker update, the Midea entry is pointed at the
  tracker's current `ip` if it differs. A move while Home Assistant was down is
  picked up at startup.
- If the tracker reports no IP (unit off the network), the last address is
  kept.
- Each tracker (MAC) can be linked once, and each Midea entry follows one
  tracker.

## Installation

The unit's Wi-Fi module must have a `device_tracker` that reports `ip` and
`mac` attributes, as router integrations do. Omada creates one for every known
Wi-Fi client but disables it by default; enable the unit's tracker first. Midea
dongles show up with host names like `net_ac_EB32`.

- **HACS:** add this repository as a custom repository (category *Integration*),
  install *Midea AC Tracker*, restart Home Assistant.
- **Manual:** copy `custom_components/midea_ac_tracker` to
  `/config/custom_components/`, restart Home Assistant.

Then, for each unit: *Settings → Devices & services → Add integration → Midea AC
Tracker*, pick the unit's Midea Smart AC entry and its device tracker.

## Development

Tests use Home Assistant's own test harness; Midea Smart AC is mocked and no unit
is contacted. They need Linux, so run them in a container:

```sh
docker run --rm -v "$PWD:/src:ro" python:3.14 bash -c \
  "cp -r /src /work && cd /work && pip install -q -r requirements_test.txt && pytest -q"
```

Validate the integration the way HACS CI does:

```sh
docker run --rm -v "$PWD:/github/workspace" ghcr.io/home-assistant/hassfest
```
