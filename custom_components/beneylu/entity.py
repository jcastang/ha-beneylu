"""Shared identity for Beneylu entities."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

class BeneyluEntity(CoordinatorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, key, child_id=None):
        super().__init__(coordinator)
        self.key = key
        self.child_id = child_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{child_id if child_id is not None else 'family'}_{key}"
    @property
    def device_info(self):
        if self.child_id is None:
            return DeviceInfo(identifiers={(DOMAIN, f"{self.coordinator.entry.entry_id}_family")},
                              name="Beneylu - Famille", manufacturer="Beneylu")
        children = self.coordinator.data["children"]
        return DeviceInfo(identifiers={(DOMAIN, f"{self.coordinator.entry.entry_id}_{self.child_id}")},
                          name=f"Beneylu - {children.get(self.child_id, self.child_id)}", manufacturer="Beneylu",
                          via_device=(DOMAIN, f"{self.coordinator.entry.entry_id}_family"))
    def posts(self):
        posts = self.coordinator.data["posts"]
        return posts if self.child_id is None else [p for p in posts if self.child_id in p["child_ids"]]
