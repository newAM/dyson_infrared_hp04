"""Support for Dyson HP04 infrared fans."""

import asyncio
from typing import Any, override

from infrared_protocols.codes.dyson.hp04 import DYSON_HP04_DEVICE_ID, DysonHP04Code
from infrared_protocols.commands.dyson import DysonPureCommand

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INFRARED_EMITTER_ENTITY_ID, DOMAIN

PARALLEL_UPDATES = 0

_SPEED_STEP_DELAY = 0.2
# A key press on the OEM remote transmits the command frame followed by two
# hold repeat frames.
_HOLD_REPEAT_COUNT = 2

_PRESET_CODES: dict[str, DysonHP04Code] = {
    "auto": DysonHP04Code.AUTO,
    "cool": DysonHP04Code.COOL,
    "night": DysonHP04Code.NIGHT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Dyson HP04 fan platform from a config entry."""
    infrared_emitter_entity_id = entry.data[CONF_INFRARED_EMITTER_ENTITY_ID]
    async_add_entities(
        [DysonInfraredHP04Fan(infrared_emitter_entity_id, entry.entry_id, entry.title)]
    )


class DysonInfraredHP04Fan(InfraredEmitterConsumerEntity, FanEntity):
    """Representation of a Dyson HP04 infrared fan entity."""

    _attr_translation_key = "fan"
    _attr_has_entity_name = True
    _attr_speed_count = 10
    _attr_assumed_state = True
    _attr_preset_modes = list(_PRESET_CODES)
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.PRESET_MODE
    )

    def __init__(
        self, infrared_emitter_entity_id: str, unique_id: str, name: str
    ) -> None:
        """Initialize the Dyson HP04 fan entity."""
        self._infrared_emitter_entity_id = infrared_emitter_entity_id

        self._attr_unique_id = unique_id
        self._attr_percentage = 50
        self._attr_is_on = False

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=name,
        )

        # The remote cycles a 2-bit rolling counter so consecutive presses of
        # the same key are not identical frames.
        self._counter = 0

    async def _async_send_dyson_action(self, code: DysonHP04Code) -> None:
        """Transmit one HP04 key press through the infrared emitter."""
        command = DysonPureCommand(
            device_id=DYSON_HP04_DEVICE_ID,
            command=code.value,
            counter=self._counter,
            repeat_count=_HOLD_REPEAT_COUNT,
        )
        await self._send_command(command)
        self._counter = (self._counter + 1) & 0b11

    def _percentage_to_speed(self, percentage: int) -> int:
        """Convert a percentage into a discrete speed level (1..speed_count)."""
        step_size = 100 / self._attr_speed_count
        return max(1, min(self._attr_speed_count, round(percentage / step_size)))

    def _speed_to_percentage(self, speed: int) -> int:
        """Convert a discrete speed level back to its normalized percentage."""
        step_size = 100 / self._attr_speed_count
        return round(speed * step_size)

    @override
    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on."""
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        # The power key is a toggle, so only transmit when tracked as off.
        if self._attr_is_on:
            return
        await self._async_send_dyson_action(DysonHP04Code.POWER)
        self._attr_is_on = True
        self.async_write_ha_state()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        # The power key is a toggle, so only transmit when tracked as on.
        if not self._attr_is_on:
            return
        await self._async_send_dyson_action(DysonHP04Code.POWER)
        self._attr_is_on = False
        self.async_write_ha_state()

    @override
    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return

        target_speed = self._percentage_to_speed(percentage)
        normalized_percentage = self._speed_to_percentage(target_speed)
        current_speed = self._percentage_to_speed(self._attr_percentage or 0)

        if target_speed == current_speed and self._attr_is_on:
            return

        if not self._attr_is_on:
            await self._async_send_dyson_action(DysonHP04Code.POWER)
            self._attr_is_on = True
            await asyncio.sleep(_SPEED_STEP_DELAY)

        code = (
            DysonHP04Code.FAN_UP
            if target_speed > current_speed
            else DysonHP04Code.FAN_DOWN
        )
        for _ in range(abs(target_speed - current_speed)):
            await self._async_send_dyson_action(code)
            await asyncio.sleep(_SPEED_STEP_DELAY)

        self._attr_percentage = normalized_percentage
        self.async_write_ha_state()

    @override
    async def async_oscillate(self, oscillating: bool) -> None:
        """Set the oscillation state of the fan."""
        # The oscillate key is a toggle, so only transmit on a state change.
        if self._attr_oscillating == oscillating:
            return
        await self._async_send_dyson_action(DysonHP04Code.OSCILLATE)
        self._attr_oscillating = oscillating
        self.async_write_ha_state()

    @override
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a fan preset mode."""
        await self._async_send_dyson_action(_PRESET_CODES[preset_mode])
        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()
