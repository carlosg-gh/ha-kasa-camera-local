# Kasa Camera (local) for Home Assistant

> **Status: early alpha.** Developed and tested against one KC100 (HA 2026.10 container).

Local control and live view of **Kasa KC100** cameras (and likely other `smartlife.cam.ipcamera` Kasa cams) from Home Assistant, with no cloud round trip. Reverse engineered from the Kasa app's LAN traffic; see [PROTOCOL.md](PROTOCOL.md).

## Features
- **Live view and snapshots** (H.264 + audio) through a private go2rtc relay.
- **Motion detection zones:** a zone editor (up to 5 four-corner zones, with a pseudo-live picture) that ships with the integration. Open it from the **Visit** link on the camera's device page, or add the card `type: custom:kasa-camera-zones` with `entity: camera.<your camera>` to any dashboard. The editor is admin-only and has no sidebar entry.
- **Switches:** camera on/off (privacy mode), status LED, motion detection, sound detection, clip audio.
- **Selects:** night vision, image rotation, power frequency, sound sensitivity.
- **Numbers:** motion sensitivity, motion minimum trigger time.
- Polls the camera every 30 s over its local HTTPS API. Setup through the UI.
- Credentials: the camera authenticates with your Kasa account email and the **MD5 hash** of the password. Only the hash is stored in Home Assistant, never the password.

## Requirements
- `ffmpeg` (used for snapshots; present in the Home Assistant container/OS images).
- A `go2rtc` binary on the Home Assistant host's `PATH` (it ships with the Home Assistant container/OS images). The integration starts its own localhost-only go2rtc process because Home Assistant's bundled go2rtc does not accept the camera's `kasa://` source.

## Not yet supported
Resolution, camera name. Night-vision values and the sensitivity ranges are partly guesses (only `auto`, 4 and 8 were observed).

## Install (HACS)
1. HACS → Custom repositories → add this repository, category **Integration**.
2. Install, restart Home Assistant.
3. Settings → Devices & services → Add integration → **Kasa Camera (local)**: camera IP (reserve it in DHCP), Kasa email, Kasa password.

Block the camera's internet access at your router afterwards if you want it fully local.

## Disclaimer
Unofficial, not affiliated with TP-Link. Interoperability work on the author's own device.
