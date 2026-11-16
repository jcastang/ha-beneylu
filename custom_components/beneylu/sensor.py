"""Family and per-child sensors."""
from homeassistant.components.sensor import SensorEntity
from .entity import BeneyluEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["beneylu"][entry.entry_id][1]
    entities = [BeneyluSensor(coordinator, "unread"), BeneyluSensor(coordinator, "posts"),
                BeneyluSensor(coordinator, "pending"), BeneyluSensor(coordinator, "notifications")]
    for child_id in coordinator.data["children"]:
        entities.extend([BeneyluSensor(coordinator, "posts", child_id), BeneyluSensor(coordinator, "pending", child_id)])
    async_add_entities(entities)

class BeneyluSensor(BeneyluEntity, SensorEntity):
    def __init__(self, coordinator, key, child_id=None):
        super().__init__(coordinator, key, child_id)
        self._attr_name = {"unread": "Messages non lus", "posts": "Mots du cahier", "pending": "Mots à signer", "notifications": "Notifications"}[key]
        self._attr_icon = {"unread": "mdi:email", "posts": "mdi:notebook", "pending": "mdi:draw-pen", "notifications": "mdi:bell"}[key]
    @property
    def native_value(self):
        if self.key == "unread":
            return self.coordinator.data["unread"]
        if self.key == "notifications":
            return len(self.coordinator.data["notifications"])
        if self.key == "posts":
            return len(self.posts())
        return sum(bool(p["pending_child_ids"] if self.child_id is None else self.child_id in p["pending_child_ids"]) for p in self.posts())
    @property
    def extra_state_attributes(self):
        if self.key == "posts":
            return {"latest": self.posts()[:10]}
        if self.key == "pending":
            return {"latest": [p for p in self.posts() if p["pending_child_ids"] and (self.child_id is None or self.child_id in p["pending_child_ids"])][:10]}
        if self.key == "notifications":
            return {"latest": self.coordinator.data["notifications"][:10]}
        return {}
