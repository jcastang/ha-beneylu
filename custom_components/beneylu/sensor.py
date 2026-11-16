"""Family and per-child sensors, including readable post content."""
from homeassistant.components.sensor import SensorEntity
from .entity import BeneyluEntity

NAMES = {
    "unread": "Messages non lus",
    "posts": "Mots du cahier",
    "pending": "Mots à signer",
    "notifications": "Notifications",
    "last_post": "Dernier mot",
    "last_notification": "Dernière notification",
}
ICONS = {
    "unread": "mdi:email", "posts": "mdi:notebook", "pending": "mdi:draw-pen",
    "notifications": "mdi:bell", "last_post": "mdi:text-box",
    "last_notification": "mdi:message-text",
}

def latest_post(posts):
    """Return newest post regardless of API ordering."""
    return max(posts, key=lambda p: (p.get("date") or "", str(p.get("id") or "")), default=None)

def latest_notification(notifications):
    """Return newest notification regardless of API ordering."""
    return max(notifications, key=lambda n: (n.get("date") or "", str(n.get("id") or "")), default=None)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["beneylu"][entry.entry_id][1]
    entities = [BeneyluSensor(coordinator, key) for key in
                ("unread", "posts", "pending", "notifications", "last_post", "last_notification")]
    for child_id in coordinator.data["children"]:
        entities.extend(BeneyluSensor(coordinator, key, child_id)
                        for key in ("posts", "pending", "last_post"))
    async_add_entities(entities)

class BeneyluSensor(BeneyluEntity, SensorEntity):
    def __init__(self, coordinator, key, child_id=None):
        super().__init__(coordinator, key, child_id)
        self._attr_name = NAMES[key]
        self._attr_icon = ICONS[key]

    @property
    def native_value(self):
        if self.key == "unread":
            return self.coordinator.data["unread"]
        if self.key == "notifications":
            return len(self.coordinator.data["notifications"])
        if self.key == "posts":
            return len(self.posts())
        if self.key == "pending":
            return sum(bool(p["pending_child_ids"] if self.child_id is None
                            else self.child_id in p["pending_child_ids"]) for p in self.posts())
        if self.key == "last_post":
            post = latest_post(self.posts())
            # Home Assistant sensor states must not exceed 255 characters.
            return (post["text"][:250] if post else None)
        if self.key == "last_notification":
            notification = latest_notification(self.coordinator.data["notifications"])
            return (notification.get("text") or "")[:250] if notification else None
        return None

    @property
    def extra_state_attributes(self):
        if self.key == "posts":
            return {"latest": sorted(self.posts(), key=lambda p: p.get("date") or "", reverse=True)[:10]}
        if self.key == "pending":
            pending = [p for p in self.posts() if p["pending_child_ids"] and
                       (self.child_id is None or self.child_id in p["pending_child_ids"])]
            return {"latest": sorted(pending, key=lambda p: p.get("date") or "", reverse=True)[:10]}
        if self.key == "notifications":
            return {"latest": sorted(self.coordinator.data["notifications"],
                                     key=lambda n: n.get("date") or "", reverse=True)[:10]}
        if self.key == "last_post":
            post = latest_post(self.posts())
            return {"text": post["text"], "date": post["date"], "children": post["children"],
                    "url": post["url"], "pending_signature_for": post["pending_signature_for"],
                    "attachments": post["attachments"]} if post else {}
        if self.key == "last_notification":
            notification = latest_notification(self.coordinator.data["notifications"])
            return {"text": notification.get("text", ""), "date": notification.get("date"),
                    "kind": notification.get("kind"), "url": notification.get("url", ""),
                    "read": notification.get("read")} if notification else {}
        return {}
