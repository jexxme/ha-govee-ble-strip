"""BLE connection handling for one Govee strip."""

from __future__ import annotations

import asyncio
import logging

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from . import protocol
from .const import ATTEMPTS, IDLE_DISCONNECT_SECONDS, NOTIFY_UUID, REPLY_TIMEOUT_SECONDS, WRITE_UUID

_LOGGER = logging.getLogger(__name__)


class StripNotFoundError(BleakError):
    """The strip is not currently seen by any connectable Bluetooth adapter."""


class GoveeStrip:
    """Talks to one strip, connecting on demand and dropping idle connections."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self._hass = hass
        self.address = address
        self.name = name
        self.state = protocol.StripState()
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._idle_timer: asyncio.TimerHandle | None = None
        self._pending: dict[tuple[int, int], asyncio.Future[bytes]] = {}

    def _ble_device(self) -> BLEDevice:
        device = bluetooth.async_ble_device_from_address(self._hass, self.address, connectable=True)
        if device is None:
            raise StripNotFoundError(f"{self.name} is not in Bluetooth range")
        return device

    async def async_read_state(self) -> protocol.StripState:
        async with self._lock:
            client = await self._connect()
            await self._refresh(client)
            self._arm_idle_timer()
            return self.state

    async def async_send(self, frames: list[bytes]) -> protocol.StripState:
        """Send command frames, then read back what the strip reports."""
        async with self._lock:
            client = await self._connect()
            for frame in frames:
                if await self._exchange(client, frame) is None:
                    _LOGGER.warning("%s did not confirm command 0x%02x", self.name, frame[1])
            await self._refresh(client)
            self._arm_idle_timer()
            return self.state

    async def async_stop(self) -> None:
        self._cancel_idle_timer()
        async with self._lock:
            await self._disconnect()

    async def _connect(self) -> BleakClientWithServiceCache:
        self._cancel_idle_timer()
        if self._client is not None and self._client.is_connected:
            return self._client
        client = await establish_connection(
            BleakClientWithServiceCache,
            self._ble_device(),
            self.name,
            disconnected_callback=self._on_disconnected,
            ble_device_callback=self._ble_device,
        )
        await client.start_notify(NOTIFY_UUID, self._on_notify)
        self._client = client
        return client

    async def _refresh(self, client: BleakClientWithServiceCache) -> None:
        for command in (protocol.CMD_POWER, protocol.CMD_BRIGHTNESS, protocol.CMD_COLOR):
            reply = await self._exchange(client, protocol.query(command))
            if reply is not None:
                self.state = protocol.apply_reply(self.state, reply)

    async def _exchange(self, client: BleakClientWithServiceCache, frame: bytes) -> bytes | None:
        """Write a frame and wait for the strip's answer, which echoes header and command.

        Right after connecting the strip ignores the first frame or two, so retry.
        """
        key = (frame[0], frame[1])
        for _ in range(ATTEMPTS):
            future: asyncio.Future[bytes] = self._hass.loop.create_future()
            self._pending[key] = future
            await client.write_gatt_char(WRITE_UUID, frame, response=False)
            try:
                return await asyncio.wait_for(future, REPLY_TIMEOUT_SECONDS)
            except TimeoutError:
                _LOGGER.debug("%s: no answer to %s", self.name, frame[:3].hex())
            finally:
                self._pending.pop(key, None)
        return None

    def _on_notify(self, _characteristic: object, data: bytearray) -> None:
        if len(data) < 2:
            return
        future = self._pending.get((data[0], data[1]))
        if future is not None and not future.done():
            future.set_result(bytes(data))

    def _on_disconnected(self, _client: object) -> None:
        self._client = None

    def _arm_idle_timer(self) -> None:
        self._cancel_idle_timer()
        self._idle_timer = self._hass.loop.call_later(
            IDLE_DISCONNECT_SECONDS,
            lambda: self._hass.async_create_background_task(self._idle_disconnect(), f"{self.name} idle disconnect"),
        )

    def _cancel_idle_timer(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None

    async def _idle_disconnect(self) -> None:
        async with self._lock:
            await self._disconnect()

    async def _disconnect(self) -> None:
        client, self._client = self._client, None
        if client is not None and client.is_connected:
            await client.disconnect()
