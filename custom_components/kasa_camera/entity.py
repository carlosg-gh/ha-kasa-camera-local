"""Shared entity base."""
from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def device_info(host: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, host)},
        name="Kasa Camera",
        manufacturer="TP-Link",
        model="KC100",
        configuration_url=f"https://{host}:10443",
    )


class KasaCamEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key: str, name: str, icon: str | None) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.data[CONF_HOST]}_{key}"
        self._attr_device_info = device_info(entry.data[CONF_HOST])
