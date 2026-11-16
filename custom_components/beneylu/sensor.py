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
    "conversations": "Conversations",
    "last_conversation": "Dernière conversation",
    "groups": "Classes et écoles",
    "account": "Compte Beneylu",
    "apps": "Applications disponibles",
    "replies": "Réponses aux mots",
    "media": "Médias du cahier",
}
ICONS = {
    "unread": "mdi:email", "posts": "mdi:notebook", "pending": "mdi:draw-pen",
    "notifications": "mdi:bell", "last_post": "mdi:text-box",
    "last_notification": "mdi:message-text",
    "conversations": "mdi:forum", "last_conversation": "mdi:message-outline",
    "groups": "mdi:school", "account": "mdi:account-school",
    "apps": "mdi:apps", "replies": "mdi:comment-text-multiple", "media": "mdi:paperclip",
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
                ("unread", "posts", "pending", "notifications", "last_post", "last_notification",
                 "conversations", "last_conversation", "groups", "account", "apps", "replies", "media")]
    for child_id in coordinator.data["children"]:
        entities.extend(BeneyluSensor(coordinator, key, child_id)
                        for key in ("posts", "pending", "last_post", "replies", "media"))
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
        if self.key == "apps":
            return sum(bool(a.get("open")) for a in self.coordinator.data.get("apps", []))
        if self.key == "replies":
            return sum(len(p.get("replies") or []) for p in self.posts())
        if self.key == "media":
            return sum(len(p.get("media") or []) for p in self.posts())
        if self.key == "groups":
            return len(self.coordinator.data.get("groups", {}))
        if self.key == "account":
            return self.coordinator.data.get("account")
        if self.key == "conversations":
            items = self.coordinator.data.get("conversations") or []
            return len(items) if isinstance(items, list) else len(items.get("conversations") or [])
        if self.key == "last_conversation":
            items = self.coordinator.data.get("conversations") or []
            if isinstance(items, dict):
                items = items.get("conversations") or []
            item = items[0] if items else None
            return str(item.get("title") or item.get("subject") or item.get("name") or item.get("id") or "")[:250] if isinstance(item, dict) else None
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
        if self.key == "apps":
            return {"applications": self.coordinator.data.get("apps", []),
                    "family_permissions": self.coordinator.data.get("family_permissions", {}),
                    "chat_permissions": self.coordinator.data.get("chat_permissions", {})}
        if self.key in ("replies", "media"):
            return {"latest": [{"post_id": p["id"], "date": p.get("date"),
                                "items": p.get(self.key, [])}
                               for p in self.posts() if p.get(self.key)][:10]}
        if self.key == "account":
            return {"children": list(self.coordinator.data.get("children", {}).values()),
                    "groups": list(self.coordinator.data.get("groups", {}).values())}
        if self.key == "groups":
            return {"names": list(self.coordinator.data.get("groups", {}).values())}
        if self.key in ("conversations", "last_conversation"):
            items = self.coordinator.data.get("conversations") or []
            if isinstance(items, dict):
                items = items.get("conversations") or []
            return {"latest": items[:10]} if self.key == "conversations" else ({"conversation": items[0]} if items else {})
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
                    "attachments": post["attachments"], "replies": post.get("replies", []),
                    "media": post.get("media", []), "interactions": post.get("interactions", [])} if post else {}
        if self.key == "last_notification":
            notification = latest_notification(self.coordinator.data["notifications"])
            return {"text": notification.get("text", ""), "date": notification.get("date"),
                    "kind": notification.get("kind"), "url": notification.get("url", ""),
                    "read": notification.get("read")} if notification else {}
        return {}
