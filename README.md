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

- Fan entity with 10 speed steps (drives the remote's fan up/down keys)
- Oscillation toggle
- Preset modes: auto, cool, night

Infrared is one-way, so all state is assumed. The power and oscillate keys are
toggles, so the integration only transmits them when its tracked state differs
from the request.

## Requirements

- Home Assistant with the `infrared` integration set up and an infrared
  emitter entity pointed at the HP04
- `infrared-protocols` with Dyson Pure (21-bit) support. The manifest pins the
  library to git until that support is released; if needed, replace the
  requirement with your own fork or branch, or install the library into the
  Home Assistant environment manually.

## Installation

Copy `custom_components/dyson_infrared_hp04` into the `custom_components`
directory of your Home Assistant configuration and restart.

## Configuration

Settings → Devices & Services → Add Integration → **Dyson Infrared HP04**,
then select the infrared emitter that faces the device.
