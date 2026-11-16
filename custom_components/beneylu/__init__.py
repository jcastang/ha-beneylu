"""Beneylu School custom integration."""
from homeassistant.const import Platform
from homeassistant.core import SupportsResponse, ServiceCall
import voluptuous as vol
from .api import BeneyluClient
from .coordinator import BeneyluCoordinator
from .const import DOMAIN, CONF_REFRESH_TOKEN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.EVENT]

async def async_setup_entry(hass, entry):
    client = BeneyluClient(entry.data.get("username"), entry.data.get("password"), entry.data.get(CONF_REFRESH_TOKEN))
    coordinator = BeneyluCoordinator(hass, entry, client)
    try:
        await coordinator.async_initialize()
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await client.close()
        raise
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (client, coordinator)
    if not hass.services.has_service(DOMAIN, "read_conversation"):
        async def read_conversation(call: ServiceCall):
            """Explicit action: remote conversation may be marked read."""
            target = call.data.get("entry_id")
            entries = hass.data.get(DOMAIN, {})
            if not target:
                if len(entries) != 1:
                    raise ValueError("Specify entry_id when multiple Beneylu accounts are configured")
                target = next(iter(entries))
            if target not in entries:
                raise ValueError("Unknown Beneylu entry_id")
            result = await entries[target][0].get_conversation(call.data["conversation_id"])
            return {"conversation": result}
        hass.services.async_register(
            DOMAIN, "read_conversation", read_conversation,
            schema=vol.Schema({vol.Required("conversation_id"): str, vol.Optional("entry_id"): str}),
            supports_response=SupportsResponse.ONLY,
        )
    if not hass.services.has_service(DOMAIN, "get_post"):
        async def get_post(call: ServiceCall):
            target = call.data.get("entry_id")
            entries = hass.data.get(DOMAIN, {})
            if not target:
                if len(entries) != 1:
                    raise ValueError("Specify entry_id when multiple Beneylu accounts are configured")
                target = next(iter(entries))
            if target not in entries:
                raise ValueError("Unknown Beneylu entry_id")
            return {"post": await entries[target][0].get_post(call.data["post_id"])}
        hass.services.async_register(
            DOMAIN, "get_post", get_post,
            schema=vol.Schema({vol.Required("post_id"): str, vol.Optional("entry_id"): str}),
            supports_response=SupportsResponse.ONLY,
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True

async def async_update_options(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    client, _ = hass.data[DOMAIN].pop(entry.entry_id)
    await client.close()
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "read_conversation")
        hass.services.async_remove(DOMAIN, "get_post")
    return True
