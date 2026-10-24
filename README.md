# Govee BLE Strip

Local Bluetooth control of Govee H6159 LED strips in Home Assistant.
No Govee cloud account, API key or LAN Control setting is needed.

## Why

The H6159 shows no "LAN Control" switch in the Govee app on older firmware, so Govee lights local cannot see it.
The remaining options were the Govee cloud or Bluetooth integrations that do not support this model.
This integration talks to the strip directly over Bluetooth, the same way the Govee app does.

## Features

- On/off, brightness (native 0-255) and RGB color.
- State is read back from the strip after every command and every 5 minutes, so changes made in the Govee app show up.
- Every command is confirmed by the strip and retried if no confirmation arrives.
- The Bluetooth connection is dropped 15 seconds after use.
  The strip accepts only one connection at a time, so this keeps it free for the Govee app and keeps adapter slots available.
- Strips are discovered automatically.

Scenes, effects and segment control are not supported.

## Requirements

- Home Assistant with a working Bluetooth adapter or an ESPHome Bluetooth proxy within range of the strip.
- A Govee H6159 strip.
  It advertises as `ihoment_H6159_XXXX`.
  Other models that share this protocol may work but are not discovered automatically.

## Installation

1. In HACS, open the menu, choose **Custom repositories**, and add `https://github.com/jexxme/ha-govee-ble-strip` with type **Integration**.
2. Download **Govee BLE Strip** and restart Home Assistant.
3. The strips appear under **Settings > Devices & services** as discovered devices.
   Click **Add** on each one.

## Troubleshooting

- If a strip shows as unavailable, another device probably holds its Bluetooth connection.
  Close the Govee app completely and wait for the next update.
- Debug logging: enable it on the integration page, or set `custom_components.govee_ble_strip: debug` under `logger:`.

## Protocol

Frames are 20 bytes: a header, a command, the payload padded with zeros to 19 bytes, and an XOR checksum.
Commands use header `0x33` and the strip echoes each one as a confirmation.
Queries use header `0xAA` and the strip answers with the current value.

| Command | Byte | Payload |
| --- | --- | --- |
| Power | `0x01` | `0x01` on, `0x00` off |
| Brightness | `0x04` | `0x00`-`0xFF` |
| Color | `0x05` | `0x02 R G B` |

Writes go to characteristic `00010203-0405-0607-0809-0a0b0c0d2b11`, replies arrive as notifications on `...2b10`.

## License

MIT
