"""Switches for the local Kasa camera."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KasaCamConfigEntry
from .const import DOMAIN, SWITCHES


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(KasaCamSwitch(coordinator, entry, *spec) for spec in SWITCHES)


class KasaCamSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, module, getter, setter, name, icon) -> None:
        super().__init__(coordinator)
        self._key, self._module, self._setter = key, module, setter
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.data[CONF_HOST]}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_HOST])},
            name="Kasa Camera",
            manufacturer="TP-Link",
            model="KC100",
            configuration_url=f"https://{entry.data[CONF_HOST]}:10443",
        )

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self._key)
        return None if value is None else value == "on"

    async def _set(self, value: str) -> None:
        await self.coordinator.api.async_call(self._module, self._setter, {"value": value})
        self.coordinator.data[self._key] = value
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set("on")

    async def async_turn_off(self, **kwargs) -> None:
        await self._set("off")
