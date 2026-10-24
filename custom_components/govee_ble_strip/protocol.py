"""Frame encoding and decoding for Govee H6159 strips.

Every frame is 20 bytes: a header byte, a command byte, the payload padded
with zeros to 19 bytes, then an XOR checksum of those 19 bytes.
Commands use header 0x33; state queries use 0xAA and the strip answers with
an 0xAA frame for the same command.
"""

from __future__ import annotations

from dataclasses import dataclass

HEADER_COMMAND = 0x33
HEADER_QUERY = 0xAA

CMD_POWER = 0x01
CMD_BRIGHTNESS = 0x04
CMD_COLOR = 0x05

COLOR_MODE_MANUAL = 0x02


@dataclass(frozen=True)
class StripState:
    """Last state the strip reported."""

    is_on: bool | None = None
    brightness: int | None = None
    rgb: tuple[int, int, int] | None = None


def build_frame(header: int, command: int, payload: bytes | list[int] = b"") -> bytes:
    """Return a checksummed 20-byte frame."""
    body = bytes([header, command, *payload])
    if len(body) > 19:
        raise ValueError("payload too long")
    body = body.ljust(19, b"\x00")
    checksum = 0
    for byte in body:
        checksum ^= byte
    return body + bytes([checksum])


def power(on: bool) -> bytes:
    return build_frame(HEADER_COMMAND, CMD_POWER, [1 if on else 0])


def brightness(value: int) -> bytes:
    """Brightness on the strip's native 0-255 scale."""
    return build_frame(HEADER_COMMAND, CMD_BRIGHTNESS, [max(1, min(255, value))])


def color(rgb: tuple[int, int, int]) -> bytes:
    return build_frame(HEADER_COMMAND, CMD_COLOR, [COLOR_MODE_MANUAL, *rgb])


def query(command: int) -> bytes:
    return build_frame(HEADER_QUERY, command)


def apply_reply(state: StripState, frame: bytes) -> StripState:
    """Fold one 0xAA reply into the state; unknown replies leave it unchanged."""
    if len(frame) < 3 or frame[0] != HEADER_QUERY:
        return state
    command = frame[1]
    if command == CMD_POWER:
        return StripState(frame[2] == 1, state.brightness, state.rgb)
    if command == CMD_BRIGHTNESS:
        return StripState(state.is_on, frame[2], state.rgb)
    if command == CMD_COLOR and frame[2] == COLOR_MODE_MANUAL and len(frame) >= 6:
        return StripState(state.is_on, state.brightness, (frame[3], frame[4], frame[5]))
    return state
