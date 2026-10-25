"""Local Bluetooth control for Govee H6159 LED strips."""

from __future__ import annotations

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import GoveeStripConfigEntry, GoveeStripCoordinator
from .device import GoveeStrip

PLATFORMS = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: GoveeStripConfigEntry) -> bool:
    device = GoveeStrip(hass, entry.data[CONF_ADDRESS], entry.title)
    coordinator = GoveeStripCoordinator(hass, entry, device)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Connecting can take a while, or fail while the Govee app holds the strip,
    # so read the first state in the background instead of blocking setup.
    entry.async_create_background_task(hass, coordinator.async_refresh(), f"{entry.title} first refresh")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoveeStripConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.device.async_stop()
    return unloaded
