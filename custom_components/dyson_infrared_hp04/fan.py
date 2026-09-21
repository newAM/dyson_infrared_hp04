"""Support for Dyson HP04 infrared fans."""

import asyncio
from typing import override

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INFRARED_EMITTER_ENTITY_ID, DOMAIN
from .entity import DysonInfraredHP04Entity
from .infrared_protocols import DysonHP04Code

PARALLEL_UPDATES = 0

_SPEED_STEP_DELAY = 0.2

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


class DysonInfraredHP04Fan(DysonInfraredHP04Entity, FanEntity):
    """Representation of a Dyson HP04 infrared fan entity."""

    _attr_translation_key = "fan"
    _attr_has_entity_name = True
    _attr_speed_count = 10
    _attr_preset_modes = list(_PRESET_CODES)
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.PRESET_MODE
    )

    def __init__(
        self, infrared_emitter_entity_id: str, unique_id: str, name: str
    ) -> None:
        """Initialize the Dyson HP04 fan entity."""
        self._infrared_emitter_entity_id = infrared_emitter_entity_id

        self._attr_unique_id = unique_id

        # Speed control is relative: remember the last commanded speed to
        # know how many fan up/down presses to send.
        self._attr_percentage = 50

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=name,
        )

    def _percentage_to_speed(self, percentage: int) -> int:
        """Convert a percentage into a discrete speed level (1..speed_count)."""
        step_size = 100 / self._attr_speed_count
        return max(1, min(self._attr_speed_count, round(percentage / step_size)))

    def _speed_to_percentage(self, speed: int) -> int:
        """Convert a discrete speed level back to its normalized percentage."""
        step_size = 100 / self._attr_speed_count
        return round(speed * step_size)

    @override
    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        # The remote has no off speed; the power key is a separate button.
        if percentage == 0:
            return

        target_speed = self._percentage_to_speed(percentage)
        normalized_percentage = self._speed_to_percentage(target_speed)
        current_speed = self._percentage_to_speed(self._attr_percentage or 0)

        if target_speed == current_speed:
            return

        code = (
            DysonHP04Code.FAN_UP
            if target_speed > current_speed
            else DysonHP04Code.FAN_DOWN
        )
        for _ in range(abs(target_speed - current_speed)):
            await self._async_send_key(code)
            await asyncio.sleep(_SPEED_STEP_DELAY)

        self._attr_percentage = normalized_percentage
        self.async_write_ha_state()

    @override
    async def async_oscillate(self, oscillating: bool) -> None:
        """Set the oscillation state of the fan."""
        # The oscillate key is a toggle, so only transmit on a state change.
        if self._attr_oscillating == oscillating:
            return
        await self._async_send_key(DysonHP04Code.OSCILLATE)
        self._attr_oscillating = oscillating
        self.async_write_ha_state()

    @override
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a fan preset mode."""
        await self._async_send_key(_PRESET_CODES[preset_mode])
        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()
