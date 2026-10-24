# Kasa Camera (local) for Home Assistant

> **Status: early alpha.** Developed and tested against one KC100 (HA 2026.10 container).

Local control and live view of **Kasa KC100** cameras (and likely other `smartlife.cam.ipcamera` Kasa cams) from Home Assistant, with no cloud round trip. Reverse engineered from the Kasa app's LAN traffic; see [PROTOCOL.md](PROTOCOL.md).

## Features
- **Live view and snapshots** (H.264 + audio) through a private go2rtc relay.
- **Switches:** camera on/off (privacy mode), status LED, motion detection, sound detection, clip audio.
- **Selects:** night vision, image rotation, power frequency, sound sensitivity.
- **Numbers:** motion sensitivity, motion minimum trigger time.
- Polls the camera every 30 s over its local HTTPS API. Setup through the UI.
- Credentials: the camera authenticates with your Kasa account email and the **MD5 hash** of the password. Only the hash is stored in Home Assistant, never the password.

## Requirements
- A `go2rtc` binary on the Home Assistant host's `PATH` (it ships with the Home Assistant container/OS images). The integration starts its own localhost-only go2rtc process because Home Assistant's bundled go2rtc does not accept the camera's `kasa://` source.

## Not yet supported
Motion detection zones, resolution, camera name. Night-vision values and the sensitivity ranges are partly guesses (only `auto`, 4 and 8 were observed).

## Install (HACS)
1. HACS → Custom repositories → add this repository, category **Integration**.
2. Install, restart Home Assistant.
3. Settings → Devices & services → Add integration → **Kasa Camera (local)**: camera IP (reserve it in DHCP), Kasa email, Kasa password.

Block the camera's internet access at your router afterwards if you want it fully local.

## Disclaimer
Unofficial, not affiliated with TP-Link. Interoperability work on the author's own device.
