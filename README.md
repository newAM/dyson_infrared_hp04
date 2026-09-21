# Dyson Infrared HP04

**WARNING:** This was built with AI with very little oversight.

A custom Home Assistant integration that controls a Dyson Pure Hot+Cool (HP04)
air purifier, fan, and heater over infrared. It builds on the built-in
[`infrared`](https://www.home-assistant.io/integrations/infrared/) integration
and sends commands through an infrared emitter entity (for example an ESPHome
`remote_transmitter`).

The IR encoding comes from the
[`infrared-protocols`](https://github.com/home-assistant-libs/infrared-protocols)
library.

## Features

- Buttons for power, fan up, fan down, and oscillate that transmit the
  corresponding remote key
- Fan entity with 10 speed steps (drives the remote's fan up/down keys)
- Oscillation toggle
- Preset modes: auto, cool, night

Entities mirror the physical remote: each control sends exactly the key press
the corresponding remote button would, and no device power state is tracked.
Speed control is relative, so the integration remembers the last speed it
commanded (restarting Home Assistant resets it). Buttons send raw key presses,
so using them (or the physical remote) does not update the fan entity's
tracked speed or oscillation.

## Requirements

- Home Assistant with the `infrared` integration set up and an infrared
  emitter entity pointed at the HP04
- `infrared-protocols` with Dyson Pure (21-bit) support. The manifest pins the
  library to the `add-dyson-hp04` branch of a fork until that support is
  released; swap the requirement for the released version once available.

## Installation

Copy `custom_components/dyson_infrared_hp04` into the `custom_components`
directory of your Home Assistant configuration and restart.

## Configuration

Settings → Devices & Services → Add Integration → **Dyson Infrared HP04**,
then select the infrared emitter that faces the device.
