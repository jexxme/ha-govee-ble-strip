"""Tests for the frame encoding, using frames captured from a real H6159."""

import importlib.util
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).parents[1] / "custom_components" / "govee_ble_strip" / "protocol.py"
_SPEC = importlib.util.spec_from_file_location("govee_ble_strip_protocol", _PATH)
protocol = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = protocol
_SPEC.loader.exec_module(protocol)


def test_power_frames_match_device_captures() -> None:
    assert protocol.power(True).hex() == "3301010000000000000000000000000000000033"
    assert protocol.power(False).hex() == "3301000000000000000000000000000000000032"


def test_color_frame_matches_device_capture() -> None:
    assert protocol.color((0, 0, 255)).hex() == "3305020000ff00000000000000000000000000cb"


def test_brightness_is_clamped_to_device_range() -> None:
    assert protocol.brightness(0)[2] == 1
    assert protocol.brightness(300)[2] == 255


def test_query_frame() -> None:
    assert protocol.query(protocol.CMD_POWER).hex() == "aa010000000000000000000000000000000000ab"


def test_payload_too_long() -> None:
    with pytest.raises(ValueError):
        protocol.build_frame(0x33, 0x01, bytes(18))


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("aa010100000000000000000000000000000000aa", protocol.StripState(is_on=True)),
        ("aa041b00000000000000000000000000000000b5", protocol.StripState(brightness=27)),
        ("aa05028b00ff00000000000000000000000000d9", protocol.StripState(rgb=(139, 0, 255))),
        ("aa06312e30372e30320000000000000000000098", protocol.StripState()),
        ("3301000000000000000000000000000000000032", protocol.StripState()),
    ],
)
def test_apply_reply(reply: str, expected: object) -> None:
    assert protocol.apply_reply(protocol.StripState(), bytes.fromhex(reply)) == expected
