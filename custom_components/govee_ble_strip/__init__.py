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
    # The strip may be busy with the Govee app; start anyway and let polling catch up.
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoveeStripConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.device.async_stop()
    return unloaded
