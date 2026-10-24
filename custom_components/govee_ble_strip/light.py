"""Light entity for a Govee strip."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol
from .const import DOMAIN, MODEL
from .coordinator import GoveeStripConfigEntry, GoveeStripCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoveeStripConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([GoveeStripLight(entry.runtime_data)])


class GoveeStripLight(CoordinatorEntity[GoveeStripCoordinator], LightEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coordinator: GoveeStripCoordinator) -> None:
        super().__init__(coordinator)
        address = coordinator.device.address
        self._attr_unique_id = dr.format_mac(address)
        self._attr_device_info = DeviceInfo(
            connections={(dr.CONNECTION_BLUETOOTH, address)},
            identifiers={(DOMAIN, address)},
            manufacturer="Govee",
            model=MODEL,
            name=coordinator.device.name,
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.is_on if self.coordinator.data else None

    @property
    def brightness(self) -> int | None:
        return self.coordinator.data.brightness if self.coordinator.data else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        return self.coordinator.data.rgb if self.coordinator.data else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        frames = [protocol.power(True)]
        if ATTR_BRIGHTNESS in kwargs:
            frames.append(protocol.brightness(kwargs[ATTR_BRIGHTNESS]))
        if ATTR_RGB_COLOR in kwargs:
            frames.append(protocol.color(kwargs[ATTR_RGB_COLOR]))
        await self.coordinator.async_send(frames)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_send([protocol.power(False)])
