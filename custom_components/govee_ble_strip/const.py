"""Constants for the Govee BLE Strip integration."""

from datetime import timedelta

DOMAIN = "govee_ble_strip"

MODEL = "H6159"
NAME_PREFIX = "ihoment_H6159"

WRITE_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"
NOTIFY_UUID = "00010203-0405-0607-0809-0a0b0c0d2b10"

# The strip accepts only one BLE connection, so drop ours soon after use to
# leave it free for the Govee app and to keep adapter slots available.
IDLE_DISCONNECT_SECONDS = 15
UPDATE_INTERVAL = timedelta(minutes=5)
REPLY_TIMEOUT_SECONDS = 1.0
ATTEMPTS = 3
