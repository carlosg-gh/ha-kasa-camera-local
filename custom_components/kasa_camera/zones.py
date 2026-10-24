"""Motion detection zones: websocket API and the bundled frontend (editor panel + card)."""
from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .api import KasaCamError
from .const import DOMAIN

PANEL_PATH = "kasa-camera-zones"
STATIC_URL = "/kasa_camera_static"
MODULE_URL = f"{STATIC_URL}/kasa-camera-zones.js"
MAX_ZONES = 5


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the JS module, load it on every dashboard (for the card) and add a hidden editor panel."""
    www = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(www), False)])
    add_extra_js_url(hass, MODULE_URL)
    # No sidebar_title: the panel is reachable by URL and from the device page, but not listed in the sidebar.
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="kasa-camera-panel",
        frontend_url_path=PANEL_PATH,
        module_url=MODULE_URL,
        require_admin=True,
    )
    websocket_api.async_register_command(hass, ws_cameras)
    websocket_api.async_register_command(hass, ws_get_zones)
    websocket_api.async_register_command(hass, ws_set_zones)


def _coordinator_for(hass: HomeAssistant, entity_id: str):
    entry = er.async_get(hass).async_get(entity_id)
    config_entry = hass.config_entries.async_get_entry(entry.config_entry_id) if entry else None
    if config_entry is None or config_entry.domain != DOMAIN or getattr(config_entry, "runtime_data", None) is None:
        raise KasaCamError(f"{entity_id} is not a loaded Kasa camera")
    return config_entry.runtime_data


@websocket_api.websocket_command({vol.Required("type"): "kasa_camera/cameras"})
@callback
def ws_cameras(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    registry = er.async_get(hass)
    cameras = [
        e.entity_id
        for e in registry.entities.values()
        if e.platform == DOMAIN and e.domain == "camera" and not e.disabled
    ]
    connection.send_result(msg["id"], cameras)


@websocket_api.websocket_command({vol.Required("type"): "kasa_camera/get_zones", vol.Required("entity_id"): str})
@websocket_api.async_response
async def ws_get_zones(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        result = await _coordinator_for(hass, msg["entity_id"]).api.async_call("motionDetect", "get_detect_area")
    except KasaCamError as err:
        connection.send_error(msg["id"], "camera_error", str(err))
        return
    connection.send_result(msg["id"], {"max": result.get("max", MAX_ZONES), "area": result.get("area", [])})


_POINT = vol.All([vol.All(vol.Coerce(int), vol.Range(min=0, max=99))], vol.Length(min=4, max=4))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "kasa_camera/set_zones",
        vol.Required("entity_id"): str,
        vol.Required("area"): vol.All([{vol.Required("x"): _POINT, vol.Required("y"): _POINT}], vol.Length(max=MAX_ZONES)),
    }
)
@websocket_api.async_response
async def ws_set_zones(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        await _coordinator_for(hass, msg["entity_id"]).api.async_call("motionDetect", "set_detect_area", {"area": msg["area"]})
    except KasaCamError as err:
        connection.send_error(msg["id"], "camera_error", str(err))
        return
    await _coordinator_for(hass, msg["entity_id"]).motion.async_load_zones()
    connection.send_result(msg["id"], {"area": msg["area"]})
