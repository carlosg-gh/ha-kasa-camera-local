"""Switches for the local Kasa camera."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KasaCamConfigEntry
from .const import SWITCHES
from .entity import KasaCamEntity


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        KasaCamSwitch(coordinator, entry, key, module, setter, name, icon)
        for key, module, _getter, setter, name, icon in SWITCHES
    )


class KasaCamSwitch(KasaCamEntity, SwitchEntity):
    def __init__(self, coordinator, entry, key, module, setter, name, icon) -> None:
        super().__init__(coordinator, entry, key, name, icon)
        self._module, self._setter = module, setter

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
