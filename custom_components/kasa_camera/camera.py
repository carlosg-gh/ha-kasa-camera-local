"""Live view for the local Kasa camera (served through a private go2rtc relay, see relay.py)."""
from __future__ import annotations

from homeassistant.components import ffmpeg
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KasaCamConfigEntry
from .entity import device_info


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([KasaCamCamera(entry)])


class KasaCamCamera(Camera):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, entry: KasaCamConfigEntry) -> None:
        super().__init__()
        host = entry.data[CONF_HOST]
        self._attr_unique_id = f"{host}_stream"
        self._attr_device_info = device_info(host)
        self._relay = entry.runtime_data.relay

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Grab a frame from the relayed stream (the camera has no still-image endpoint)."""
        url = await self._relay.async_url(self.hass)
        return await ffmpeg.async_get_image(self.hass, url, width=width, height=height)

    async def stream_source(self) -> str | None:
        return await self._relay.async_url(self.hass)

