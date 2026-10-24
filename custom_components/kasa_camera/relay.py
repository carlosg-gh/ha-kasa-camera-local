"""Private go2rtc relay that turns the camera's proprietary stream into a local RTSP stream.

Home Assistant's own go2rtc only accepts a fixed list of source types (no ``kasa://``), so the camera is read by a
second go2rtc process bound to localhost and exposed as ``rtsp://127.0.0.1:<port>/camera``.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import shutil
import socket
import tempfile

_LOGGER = logging.getLogger(__name__)
_BINARIES = ("/bin/go2rtc", "/usr/bin/go2rtc", "/usr/local/bin/go2rtc")


def find_go2rtc() -> str | None:
    return shutil.which("go2rtc") or next((p for p in _BINARIES if os.path.exists(p)), None)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Go2RtcRelay:
    def __init__(self, source: str) -> None:
        self._source = source
        self._proc: asyncio.subprocess.Process | None = None
        self._dir: str | None = None
        self._rtsp_port = 0
        self._lock = asyncio.Lock()

    def _write_config(self) -> None:
        self._dir = tempfile.mkdtemp(prefix="kasa-go2rtc-")
        self._rtsp_port = _free_port()
        cfg = (
            f"api:\n  listen: \"127.0.0.1:{_free_port()}\"\n"
            f"rtsp:\n  listen: \"127.0.0.1:{self._rtsp_port}\"\n"
            f"webrtc:\n  listen: \"127.0.0.1:{_free_port()}\"\n"
            f"log:\n  level: warn\n"
            f"streams:\n  camera: \"{self._source}\"\n"
        )
        fd = os.open(os.path.join(self._dir, "go2rtc.yaml"), os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(cfg)

    async def async_url(self, hass) -> str | None:
        """Start the relay if needed and return its RTSP URL."""
        async with self._lock:
            if self._proc is not None and self._proc.returncode is None:
                return f"rtsp://127.0.0.1:{self._rtsp_port}/camera"
            binary = await hass.async_add_executor_job(find_go2rtc)
            if binary is None:
                _LOGGER.warning("go2rtc binary not found; the live view needs go2rtc installed")
                return None
            await self._cleanup(hass)
            await hass.async_add_executor_job(self._write_config)
            self._proc = await asyncio.create_subprocess_exec(
                binary, "-c", os.path.join(self._dir, "go2rtc.yaml"),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            for _ in range(50):
                with contextlib.suppress(OSError):
                    _r, w = await asyncio.open_connection("127.0.0.1", self._rtsp_port)
                    w.close()
                    break
                await asyncio.sleep(0.1)
            return f"rtsp://127.0.0.1:{self._rtsp_port}/camera"

    async def _cleanup(self, hass) -> None:
        if self._proc is not None and self._proc.returncode is None:
            self._proc.terminate()
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._proc.wait(), 5)
        self._proc = None
        if self._dir:
            await hass.async_add_executor_job(shutil.rmtree, self._dir, True)
            self._dir = None

    async def async_stop(self, hass) -> None:
        async with self._lock:
            await self._cleanup(hass)
