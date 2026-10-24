"""Motion sensor for the local Kasa camera (see motion.py)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KasaCamConfigEntry
from .entity import device_info


async def async_setup_entry(hass: HomeAssistant, entry: KasaCamConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([KasaCamMotion(entry)])


class KasaCamMotion(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Motion"
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_should_poll = False

    def __init__(self, entry: KasaCamConfigEntry) -> None:
        self._detector = entry.runtime_data.motion
        self._attr_unique_id = f"{entry.data[CONF_HOST]}_motion_sensor"
        self._attr_device_info = device_info(entry.data[CONF_HOST])

    @property
    def is_on(self) -> bool:
        return self._detector.is_on

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._detector.add_listener(self.schedule_update_ha_state))
