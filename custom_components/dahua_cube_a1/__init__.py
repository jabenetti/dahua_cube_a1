"""Home Assistant integration for Dahua Cube A1 cameras."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
from .camera import Camera
from .proxy import start_proxy


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    username = entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)
    password = entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
    proxy_port = entry.data.get(CONF_PROXY_PORT, DEFAULT_PROXY_PORT)

    camera_ips = entry.data.get(CONF_CAMERAS, [])
    cameras_list = []
    for idx, ip in enumerate(camera_ips):
        camera = Camera(ip=ip, username=username, password=password, name=f"Camera {idx}", index=idx)
        if camera.login():
            cameras_list.append(camera)

    runner, proxy_task = start_proxy(proxy_port, username, password, cameras_list)
    hass.data[DOMAIN][entry.entry_id] = {
        "cameras": cameras_list,
        "proxy_runner": runner,
        "proxy_task": proxy_task,
    }

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, {})
    cameras_list = data.get("cameras", [])
    runner = data.get("proxy_runner")
    proxy_task = data.get("proxy_task")

    for cam in cameras_list:
        cam.logout()

    if runner:
        await runner.cleanup()

    if proxy_task:
        proxy_task.cancel()
        try:
            await proxy_task
        except asyncio.CancelledError:
            pass

    return True