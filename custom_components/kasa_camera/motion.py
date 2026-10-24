"""Local motion detection: frame differencing on the relayed stream, limited to the camera's motion zones.

The camera only reports motion to the TP-Link cloud, so Home Assistant works it out from the video itself.
ffmpeg downsizes the stream to a tiny grayscale picture; consecutive pictures are compared inside the zones.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import time

from homeassistant.components.ffmpeg import get_ffmpeg_manager
from homeassistant.core import HomeAssistant

from .api import KasaCamError

_LOGGER = logging.getLogger(__name__)

W, H, FPS = 64, 48, 4
HOLD = 10.0  # seconds without motion before the sensor clears
GAP = 1.0  # motion that pauses longer than this restarts the minimum trigger time
RETRY = 15


def _inside(poly_x: list[int], poly_y: list[int], px: float, py: float) -> bool:
    inside = False
    j = len(poly_x) - 1
    for i in range(len(poly_x)):
        if (poly_y[i] > py) != (poly_y[j] > py) and px < (poly_x[j] - poly_x[i]) * (py - poly_y[i]) / (poly_y[j] - poly_y[i]) + poly_x[i]:
            inside = not inside
        j = i
    return inside


class MotionDetector:
    def __init__(self, hass: HomeAssistant, coordinator) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._task: asyncio.Task | None = None
        self._mask: list[int] = list(range(W * H))
        self._listeners: list[Callable[[], None]] = []
        self.is_on = False

    def add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    def _set(self, value: bool) -> None:
        if value != self.is_on:
            self.is_on = value
            for cb in list(self._listeners):
                cb()

    @property
    def enabled(self) -> bool:
        data = self._coordinator.data
        return data.get("motion") == "on" and data.get("camera") != "off"

    def sync(self) -> None:
        """Start or stop detection to match the motion detection switch (called on every coordinator update)."""
        if self.enabled and self._task is None:
            self._task = self._hass.async_create_background_task(self._run(), "kasa_camera motion detection")
        elif not self.enabled and self._task is not None:
            self.stop()

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._set(False)

    async def async_load_zones(self) -> None:
        try:
            area = (await self._coordinator.api.async_call("motionDetect", "get_detect_area")).get("area", [])
        except KasaCamError as err:
            _LOGGER.debug("Could not read zones: %s", err)
            return
        if not area:
            self._mask = list(range(W * H))
            return
        mask = []
        for y in range(H):
            for x in range(W):
                px, py = (x + 0.5) * 100 / W, (y + 0.5) * 100 / H
                if any(_inside(z["x"], z["y"], px, py) for z in area):
                    mask.append(y * W + x)
        self._mask = mask

    def _thresholds(self) -> tuple[int, float, float]:
        data = self._coordinator.data
        level = min(max(int(data.get("motion_level") or 5), 1), 10)
        pixel = 40 - 3 * level  # brightness change that counts for a pixel (higher level = more sensitive)
        fraction = 0.03 - 0.0025 * level  # share of the zone that must change
        minimum = (data.get("motion_trigger") or 2000) / 1000
        return pixel, fraction, minimum

    async def _run(self) -> None:
        while True:
            try:
                await self.async_load_zones()
                url = await self._coordinator.relay.async_url(self._hass)
                await self._watch(url)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - keep the detector alive across stream hiccups
                _LOGGER.debug("Motion detection stream ended: %s", err)
            self._set(False)
            await asyncio.sleep(RETRY)

    async def _watch(self, url: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            get_ffmpeg_manager(self._hass).binary, "-nostdin", "-loglevel", "error",
            "-rtsp_transport", "tcp", "-i", url, "-an",
            "-vf", f"fps={FPS},scale={W}:{H}:flags=area", "-pix_fmt", "gray", "-f", "rawvideo", "-",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        prev: bytes | None = None
        first = last = None
        try:
            while True:
                frame = await asyncio.wait_for(proc.stdout.readexactly(W * H), 20)
                now = time.monotonic()
                if prev is not None and self._mask:
                    pixel, fraction, minimum = self._thresholds()
                    changed = sum(1 for i in self._mask if abs(frame[i] - prev[i]) > pixel)
                    share = changed / len(self._mask)
                    # A change of nearly the whole picture is exposure or IR switching, not movement.
                    if fraction <= share < 0.7:
                        last = now
                        if first is None:
                            first = now
                    elif first is not None and last is not None and now - last > GAP and not self.is_on:
                        first = None
                    if not self.is_on and first is not None and now - first >= minimum:
                        self._set(True)
                    if self.is_on and last is not None and now - last > HOLD:
                        self._set(False)
                        first = None
                prev = frame
        finally:
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
