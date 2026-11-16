"""Signature pending binary sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .entity import BeneyluEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["beneylu"][entry.entry_id][1]
    async_add_entities([BeneyluSignature(coordinator)] + [BeneyluSignature(coordinator, c) for c in coordinator.data["children"]])

class BeneyluSignature(BeneyluEntity, BinarySensorEntity):
    _attr_name = "Signature en attente"
    _attr_icon = "mdi:signature-freehand"
    def __init__(self, coordinator, child_id=None):
        super().__init__(coordinator, "signature", child_id)
    @property
    def is_on(self):
        return any(p["pending_child_ids"] if self.child_id is None else self.child_id in p["pending_child_ids"] for p in self.posts())
