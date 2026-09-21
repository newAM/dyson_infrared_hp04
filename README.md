# Dyson Infrared HP04

**WARNING:** This was built with AI with very little oversight.

A custom Home Assistant integration that controls a Dyson Pure Hot+Cool (HP04)
air purifier, fan, and heater over infrared. It builds on the built-in
[`infrared`](https://www.home-assistant.io/integrations/infrared/) integration
and sends commands through an infrared emitter entity (for example an ESPHome
`remote_transmitter`).

## Features

Buttons for:

- Power
- Speed up
- Speed down
- Oscillate

## Requirements

- Home Assistant with the `infrared` integration set up and an infrared
  emitter entity pointed at the HP04.

## Installation

Copy `custom_components/dyson_infrared_hp04` into the `custom_components`
directory of your Home Assistant configuration and restart.

## Configuration

Settings → Devices & Services → Add Integration → **Dyson Infrared HP04**,
then select the infrared emitter that faces the device.
