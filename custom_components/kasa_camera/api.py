"""Client for the KC100 local API (see configs/kasa/kc100-local-api.md)."""
from __future__ import annotations

import base64
import json
import ssl
import urllib.parse
import urllib.request
import uuid

from homeassistant.core import HomeAssistant

AUTH_ERROR = -10007


class KasaCamError(Exception):
    """Camera unreachable or returned an error."""


class KasaCamAuthError(KasaCamError):
    """Credentials rejected."""


def _enc(data: bytes) -> bytes:
    key, out = 171, bytearray()
    for c in data:
        key ^= c
        out.append(key)
    return bytes(out)


def _dec(data: bytes) -> bytes:
    key, out = 171, bytearray()
    for c in data:
        out.append(c ^ key)
        key = c
    return bytes(out)


def _ssl_context() -> ssl.SSLContext:
    # The camera presents a self-signed certificate with a weak key.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    return ctx


class KasaCamApi:
    """Blocking calls run in the executor."""

    def __init__(self, hass: HomeAssistant, host: str, username: str, password_md5: str) -> None:
        self._hass = hass
        self._host = host
        self._auth = base64.b64encode(f"{username}:{password_md5}".encode()).decode()
        self._ctx = _ssl_context()

    def _call(self, module: str, method: str, args: dict | None) -> dict:
        msg = {f"smartlife.cam.ipcamera.{module}": {method: args or {}}, "context": {"source": str(uuid.uuid4())}}
        body = urllib.parse.urlencode(
            {"content": base64.b64encode(_enc(json.dumps(msg, separators=(",", ":")).encode())).decode()}
        ).encode()
        req = urllib.request.Request(f"https://{self._host}:10443/data/LINKIE.json", body)
        req.add_header("Authorization", f"Basic {self._auth}")
        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=8) as resp:
                reply = json.loads(_dec(base64.b64decode(resp.read())))
        except (OSError, ValueError) as err:
            raise KasaCamError(str(err)) from err
        result = reply.get(f"smartlife.cam.ipcamera.{module}", {}).get(method, {})
        code = result.get("err_code", 0)
        if code == AUTH_ERROR:
            raise KasaCamAuthError("Unauthorized")
        if code:
            raise KasaCamError(f"{module}.{method} err_code {code}")
        return result

    async def async_call(self, module: str, method: str, args: dict | None = None) -> dict:
        return await self._hass.async_add_executor_job(self._call, module, method, args)
