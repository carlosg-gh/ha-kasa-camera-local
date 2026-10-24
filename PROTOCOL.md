# Kasa KC100 local control protocol (reverse engineered 2026-10-24)

Camera at `<camera-ip>` (give it a DHCP reservation). Captured with mitmproxy between the Kasa Android app and the camera.

## Transport
- `POST https://<camera-ip>:10443/data/LINKIE.json` (self-signed cert with a weak key: use `curl -k`, and `ssl_insecure` in proxies).
- Form body `content=<urlencoded base64>`; response body is base64 only.
- Payload = JSON encrypted with the TP-Link XOR autokey cipher (initial key 171, `out = key ^ byte; key = out` on encrypt; on decrypt `out = key ^ byte; key = byte`), then base64.
- JSON requests carry `"context":{"source":"<uuid>"}`; any uuid appears to be accepted (not verified).
- Authentication: HTTP basic (Kasa account, same as the video stream) with the Kasa account email and the MD5 hex digest (32 chars) of the account password; verified working. Video: `https://<camera-ip>:19443/https/stream/mixed`.

## Commands (module `smartlife.cam.ipcamera.<x>`; every reply has `err_code: 0` on success)
| Module | get | set |
|---|---|---|
| switch | `get_is_enable` -> `value` on/off (privacy mode: off = camera disabled) | `set_is_enable {value}` |
| led | `get_status` -> on/off | `set_status {value}` |
| videoControl | `get_rotation_degree`, `get_power_frequency` | `set_rotation_degree {value: 0/180}`, `set_resolution {value:[{channel:1,resolution:"1080P"}]}`, `set_power_frequency {value: 50/60}` |
| dayNight | `get_mode` -> auto/on/off | `set_mode {value}` |
| motionDetect | `get_is_enable`, `get_sensitivity`, `get_sensitivity_level`, `get_min_trigger_time`, `get_detect_area` | `set_is_enable`, `set_sensitivity_level {day_mode_level, night_mode_level}`, `set_min_trigger_time {day_mode_value, night_mode_value}` (ms), `set_detect_area {area:[{x:[4],y:[4]}]}` |
| soundDetect | `get_is_enable`, `get_sensitivity` | `set_is_enable`, `set_sensitivity {value}` |
| delivery | `get_clip_audio_is_enable` | `set_clip_audio_is_enable {value}` |
| system | | `set_alias {value}` |
| wireless / dateTime | `get_uplink`, `get_time_zone`, `get_time` | |

Request example: `{"smartlife.cam.ipcamera.led":{"set_status":{"value":"off"}},"context":{"source":"<uuid>"}}`
