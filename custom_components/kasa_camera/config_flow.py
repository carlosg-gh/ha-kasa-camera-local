"""Config flow: asks for the Kasa account; stores only the MD5 hash the camera expects."""
from __future__ import annotations

import hashlib

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import KasaCamApi, KasaCamAuthError, KasaCamError
from .const import CONF_PASSWORD_HASH, DOMAIN

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
    }
)


class KasaCameraConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            pw_hash = hashlib.md5(user_input[CONF_PASSWORD].encode()).hexdigest()
            api = KasaCamApi(self.hass, user_input[CONF_HOST], user_input[CONF_USERNAME], pw_hash)
            try:
                await api.async_call("led", "get_status")
            except KasaCamAuthError:
                errors["base"] = "invalid_auth"
            except KasaCamError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Kasa Camera {user_input[CONF_HOST]}",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD_HASH: pw_hash,
                    },
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)
