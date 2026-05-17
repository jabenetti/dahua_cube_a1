"""Config flow for Dahua Cube A1 integration."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_CAMERAS,
    CONF_PROXY_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_PROXY_PORT,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
)


class DahuaCubeA1ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dahua Cube A1."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Parse camera IPs (one per line)
            cameras_raw = user_input[CONF_CAMERAS].strip()
            camera_ips = [ip.strip() for ip in cameras_raw.splitlines() if ip.strip()]

            if not camera_ips:
                errors["base"] = "no_cameras"
            else:
                data = {
                    CONF_PROXY_PORT: user_input[CONF_PROXY_PORT],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_CAMERAS: camera_ips,
                }

                await self.async_set_unique_id(f"{camera_ips[0]}_{user_input[CONF_USERNAME]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Dahua Cube A1 ({len(camera_ips)} cameras)",
                    data=data,
                )

        # Default form with one IP per line
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROXY_PORT, default=DEFAULT_PROXY_PORT): cv.port,
                vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
                vol.Required(
                    CONF_CAMERAS,
                    default="192.168.1.100",
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "cameras_help": "Enter one camera IP per line"
            },
        )