"""Beneylu School custom integration."""
from homeassistant.const import Platform
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
    return True
