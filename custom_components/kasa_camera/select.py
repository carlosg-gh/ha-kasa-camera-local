"""Selects for the local Kasa camera."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KasaCamConfigEntry
from .const import SELECTS
from .entity import KasaCamEntity


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        KasaCamSelect(coordinator, entry, key, name, icon, options, module, setter)
        for key, name, icon, options, module, _getter, setter in SELECTS
    )


class KasaCamSelect(KasaCamEntity, SelectEntity):
    def __init__(self, coordinator, entry, key, name, icon, options, module, setter) -> None:
        super().__init__(coordinator, entry, key, name, icon)
        self._map = options
        self._module, self._setter = module, setter
        self._attr_options = list(options)

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get(self._key)
        return next((label for label, value in self._map.items() if value == raw), None)

    async def async_select_option(self, option: str) -> None:
        raw = self._map[option]
        await self.coordinator.api.async_call(self._module, self._setter, {"value": raw})
        self.coordinator.data[self._key] = raw
        self.async_write_ha_state()
