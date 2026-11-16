"""Coordinated polling and durable event deduplication."""
from __future__ import annotations
import hashlib
import json
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store
from .api import BeneyluError, BeneyluAuthError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

def fingerprint(item):
    # Pending signature changes cause the post to be reported as changed.
    payload = {k: item.get(k) for k in ("id", "text", "date", "pending_child_ids", "attachments")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def changes(previous, posts, notifications):
    current = {f"post:{p['id']}": fingerprint(p) for p in posts}
    current.update({f"notification:{n['id']}": str(n['id']) for n in notifications if n.get("id") is not None})
    updated = [k for k, value in current.items() if k not in previous or previous[k] != value]
    return current, updated

class BeneyluCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(hass, logger=__import__("logging").getLogger(__name__),
                         name=f"Beneylu {entry.entry_id}",
                         update_interval=timedelta(minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
        self.entry = entry
        self.client = client
        self.store = Store(hass, 1, f"beneylu_{entry.entry_id}")
        self.seen = {}
        self.initialized = False
        self.events = []

    async def async_initialize(self):
        stored = await self.store.async_load() or {}
        self.seen = stored.get("seen", {})
        self.initialized = bool(stored.get("initialized"))

    async def _async_update_data(self):
        try:
            data = await self.client.fetch()
        except BeneyluAuthError as exc:
            from homeassistant.exceptions import ConfigEntryAuthFailed
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except (BeneyluError, ValueError, KeyError, TypeError) as exc:
            raise UpdateFailed(str(exc)) from exc
        new_seen, changed = changes(self.seen, data["posts"], data["notifications"])
        self.events = changed if self.initialized else []
        self.seen = new_seen
        self.initialized = True
        await self.store.async_save({"seen": self.seen, "initialized": True})
        for key in self.events:
            kind, item_id = key.split(":", 1)
            item = next((p for p in data["posts"] if str(p["id"]) == item_id), None) if kind == "post" else next((n for n in data["notifications"] if str(n.get("id")) == item_id), None)
            if item is not None:
                self.hass.bus.async_fire(f"beneylu_{'post' if kind == 'post' else 'notification'}_changed", {
                    "entry_id": self.entry.entry_id, "id": item_id,
                    "children": item.get("children", []) if kind == "post" else [],
                    "url": item.get("url", ""), "text": (item.get("text") or item.get("content") or "")[:500],
                })
        return data
