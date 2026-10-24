"""Local control for Kasa cameras (KC100) over the camera's LAN API."""
from __future__ import annotations

from datetime import timedelta
import logging
from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KasaCamApi, KasaCamAuthError, KasaCamError
from .const import CONF_PASSWORD_HASH, DOMAIN, FETCH, PLATFORMS, STREAM_PORT
from .motion import MotionDetector
from .relay import Go2RtcRelay
from .zones import async_setup_frontend

_LOGGER = logging.getLogger(__name__)

type KasaCamConfigEntry = ConfigEntry[DataUpdateCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    await async_setup_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry) -> bool:
    api = KasaCamApi(hass, entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD_HASH])

    async def _update() -> dict[str, object]:
        data: dict[str, object] = {}
        last_error: KasaCamError | None = None
        for key, module, getter, field in FETCH:
            try:
                data[key] = (await api.async_call(module, getter)).get(field)
            except KasaCamAuthError as err:
                raise ConfigEntryAuthFailed from err
            except KasaCamError as err:
                # One unsupported getter must not take the whole camera offline.
                _LOGGER.debug("%s.%s failed: %s", module, getter, err)
                data[key] = None
                last_error = err
        if last_error is not None and all(v is None for v in data.values()):
            raise UpdateFailed(str(last_error))
        return data

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, config_entry=entry, name=DOMAIN, update_method=_update, update_interval=timedelta(seconds=30)
    )
    coordinator.api = api  # type: ignore[attr-defined]
    await coordinator.async_config_entry_first_refresh()
    # go2rtc's kasa source sends the "password" as the basic-auth password, which for the KC100 is the MD5 hex.
    user = quote(entry.data[CONF_USERNAME], safe="")
    host = entry.data[CONF_HOST]
    coordinator.relay = Go2RtcRelay(  # type: ignore[attr-defined]
        f"kasa://{user}:{entry.data[CONF_PASSWORD_HASH]}@{host}:{STREAM_PORT}/https/stream/mixed?video=H264&audio=G711"
    )
    coordinator.motion = MotionDetector(hass, coordinator)  # type: ignore[attr-defined]
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_add_listener(coordinator.motion.sync))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.motion.sync()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KasaCamConfigEntry) -> bool:
    entry.runtime_data.motion.stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.relay.async_stop(hass)
    return unloaded
