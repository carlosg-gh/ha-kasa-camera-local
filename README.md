# Kasa Camera (local) for Home Assistant

> **Status: early alpha.** Developed against one KC100; the Home Assistant side has had limited testing.

Local control of **Kasa KC100** cameras (and likely other `smartlife.cam.ipcamera` Kasa cams) from Home Assistant, with no cloud round trip. Reverse engineered from the Kasa app's LAN traffic; see [PROTOCOL.md](PROTOCOL.md).

## Features
- Switches: camera on/off (privacy mode), status LED, motion detection, sound detection, clip audio.
- Polls the camera every 30 s over its local HTTPS API. Setup through the UI.
- Credentials: the camera authenticates with your Kasa account email and the **MD5 hash** of the password. Only the hash is stored in Home Assistant, never the password.

## Not yet supported
Video (use go2rtc/ffmpeg with `https://<camera-ip>:19443/https/stream/mixed?video=H264&audio=G711`, same basic-auth login), day/night mode, motion zones and sensitivity, rotation. Tested on a KC100 only.

## Install (HACS)
1. HACS → Custom repositories → add this repository, category **Integration**.
2. Install, restart Home Assistant.
3. Settings → Devices & services → Add integration → **Kasa Camera (local)**: camera IP (reserve it in DHCP), Kasa email, Kasa password.

Block the camera's internet access at your router afterwards if you want it fully local.

## Disclaimer
Unofficial, not affiliated with TP-Link. Interoperability work on the author's own device.
