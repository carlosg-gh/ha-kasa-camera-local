"""Constants for the local Kasa camera integration."""
from homeassistant.const import Platform

DOMAIN = "kasa_camera"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.CAMERA, Platform.NUMBER, Platform.SELECT, Platform.SWITCH]
CONF_PASSWORD_HASH = "password_md5"
STREAM_PORT = 19443

# key, module, getter, setter, name, icon
SWITCHES = [
    ("camera", "switch", "get_is_enable", "set_is_enable", "Camera", "mdi:cctv"),
    ("led", "led", "get_status", "set_status", "Status LED", "mdi:led-on"),
    ("motion", "motionDetect", "get_is_enable", "set_is_enable", "Motion detection", "mdi:motion-sensor"),
    ("sound", "soundDetect", "get_is_enable", "set_is_enable", "Sound detection", "mdi:ear-hearing"),
    ("clip_audio", "delivery", "get_clip_audio_is_enable", "set_clip_audio_is_enable", "Clip audio", "mdi:microphone"),
]

# key, name, icon, {label: camera value}, module, getter, setter
SELECTS = [
    ("day_night", "Night vision", "mdi:weather-night", {"auto": "auto", "on": "on", "off": "off"}, "dayNight", "get_mode", "set_mode"),
    ("rotation", "Image rotation", "mdi:rotate-3d-variant", {"normal": 0, "flipped": 180}, "videoControl", "get_rotation_degree", "set_rotation_degree"),
    ("power_freq", "Power frequency", "mdi:sine-wave", {"50 Hz": 50, "60 Hz": 60}, "videoControl", "get_power_frequency", "set_power_frequency"),
    ("sound_sens", "Sound sensitivity", "mdi:volume-high", {"low": "low", "medium": "medium", "high": "high"}, "soundDetect", "get_sensitivity", "set_sensitivity"),
]

# key, name, icon, min, max, step, unit, module, getter, response field, setter, setter args (value -> dict)
NUMBERS = [
    (
        "motion_level", "Motion sensitivity", "mdi:tune", 1, 10, 1, None,
        "motionDetect", "get_sensitivity_level", "day_mode_level", "set_sensitivity_level",
        lambda v: {"day_mode_level": int(v), "night_mode_level": int(v)},
    ),
    (
        "motion_trigger", "Motion minimum trigger time", "mdi:timer-outline", 0.5, 5, 0.1, "s",
        "motionDetect", "get_min_trigger_time", "day_mode_value", "set_min_trigger_time",
        lambda v: {"day_mode_value": int(v * 1000), "night_mode_value": int(v * 1000)},
    ),
]

# Everything the coordinator polls: key, module, getter, response field
FETCH = (
    [(k, m, g, "value") for k, m, g, *_ in SWITCHES]
    + [(k, m, g, "value") for k, _n, _i, _o, m, g, _s in SELECTS]
    + [(n[0], n[7], n[8], n[9]) for n in NUMBERS]
)
