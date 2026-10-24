"""Numbers for the local Kasa camera."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KasaCamConfigEntry
from .const import NUMBERS
from .entity import KasaCamEntity


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(KasaCamNumber(coordinator, entry, *spec) for spec in NUMBERS)


class KasaCamNumber(KasaCamEntity, NumberEntity):
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, entry, key, name, icon, vmin, vmax, step, unit, module, _getter, _field, setter, args) -> None:
        super().__init__(coordinator, entry, key, name, icon)
        self._attr_native_min_value = vmin
        self._attr_native_max_value = vmax
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._module, self._setter, self._args = module, setter, args
        self._seconds = unit == "s"

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self._key)
        if raw is None:
            return None
        return raw / 1000 if self._seconds else raw

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.async_call(self._module, self._setter, self._args(value))
        self.coordinator.data[self._key] = int(value * 1000) if self._seconds else int(value)
        self.async_write_ha_state()
