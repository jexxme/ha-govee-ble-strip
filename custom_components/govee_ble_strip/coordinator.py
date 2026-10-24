"""Polling coordinator for one Govee strip."""

from __future__ import annotations

import logging

from bleak.exc import BleakError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL
from .device import GoveeStrip
from .protocol import StripState

_LOGGER = logging.getLogger(__name__)

type GoveeStripConfigEntry = ConfigEntry[GoveeStripCoordinator]


class GoveeStripCoordinator(DataUpdateCoordinator[StripState]):
    """Reads the strip's state now and then, and after every command."""

    def __init__(self, hass: HomeAssistant, entry: GoveeStripConfigEntry, device: GoveeStrip) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=device.name, update_interval=UPDATE_INTERVAL)
        self.device = device

    async def _async_update_data(self) -> StripState:
        try:
            return await self.device.async_read_state()
        except (BleakError, TimeoutError) as err:
            raise UpdateFailed(f"{self.device.name} not reachable: {err}") from err

    async def async_send(self, frames: list[bytes]) -> None:
        try:
            state = await self.device.async_send(frames)
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"{self.device.name} not reachable: {err}") from err
        self.async_set_updated_data(state)
