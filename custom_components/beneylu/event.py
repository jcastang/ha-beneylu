"""Event entities for most recent changes (also emits HA bus events)."""
from homeassistant.components.event import EventEntity
from homeassistant.core import callback
from .entity import BeneyluEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["beneylu"][entry.entry_id][1]
    async_add_entities([BeneyluEvent(coordinator, "post"), BeneyluEvent(coordinator, "notification")])

class BeneyluEvent(BeneyluEntity, EventEntity):
    def __init__(self, coordinator, kind):
        super().__init__(coordinator, f"event_{kind}")
        self.kind = kind
        self._attr_name = "Changement cahier" if kind == "post" else "Nouvelle notification"
        self._attr_event_types = ["changed"]
        self._processed = set(coordinator.events)
    @callback
    def _handle_coordinator_update(self):
        for key in self.coordinator.events:
            if key.startswith(f"{self.kind}:") and key not in self._processed:
                self._trigger_event("changed", {"id": key.split(":", 1)[1]})
                self.async_write_ha_state()
        self._processed = set(self.coordinator.events)
        super()._handle_coordinator_update()
