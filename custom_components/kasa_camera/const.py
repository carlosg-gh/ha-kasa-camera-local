"""Constants for the local Kasa camera integration."""
from homeassistant.const import Platform

DOMAIN = "kasa_camera"
PLATFORMS = [Platform.SWITCH]
CONF_PASSWORD_HASH = "password_md5"

# key, module, getter, setter, name, icon
SWITCHES = [
    ("camera", "switch", "get_is_enable", "set_is_enable", "Camera", "mdi:cctv"),
    ("led", "led", "get_status", "set_status", "Status LED", "mdi:led-on"),
    ("motion", "motionDetect", "get_is_enable", "set_is_enable", "Motion detection", "mdi:motion-sensor"),
    ("sound", "soundDetect", "get_is_enable", "set_is_enable", "Sound detection", "mdi:ear-hearing"),
    ("clip_audio", "delivery", "get_clip_audio_is_enable", "set_clip_audio_is_enable", "Clip audio", "mdi:microphone"),
]
