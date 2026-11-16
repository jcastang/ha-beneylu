"""UI configuration and options."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from .api import BeneyluClient, BeneyluAuthError, BeneyluError
from .const import DOMAIN, CONF_REFRESH_TOKEN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

class BeneyluConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            client = BeneyluClient(user_input.get(CONF_USERNAME), user_input.get(CONF_PASSWORD), user_input.get(CONF_REFRESH_TOKEN))
            try:
                account = await client.get("/api/auth/users/me")
            except BeneyluAuthError:
                errors["base"] = "invalid_auth"
            except BeneyluError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(account.get("id") or user_input.get(CONF_USERNAME) or "token-account"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=account.get("displayName") or "Beneylu", data=user_input)
            finally:
                await client.close()
        schema = vol.Schema({vol.Optional(CONF_USERNAME, default=""): str,
                             vol.Optional(CONF_PASSWORD, default=""): str,
                             vol.Optional(CONF_REFRESH_TOKEN, default=""): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return BeneyluOptionsFlow()

class BeneyluOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=180))}))
