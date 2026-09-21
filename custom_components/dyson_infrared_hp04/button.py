"""Support for Dyson HP04 infrared buttons."""

from typing import override

from infrared_protocols.codes.dyson.hp04 import DysonHP04Code

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_INFRARED_EMITTER_ENTITY_ID, DOMAIN
from .entity import DysonInfraredHP04Entity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Dyson HP04 button platform from a config entry."""
    infrared_emitter_entity_id = entry.data[CONF_INFRARED_EMITTER_ENTITY_ID]
    async_add_entities(
        [
            DysonInfraredHP04PowerButton(
                infrared_emitter_entity_id, entry.entry_id, entry.title
            )
        ]
    )


class DysonInfraredHP04PowerButton(DysonInfraredHP04Entity, ButtonEntity):
    """Representation of a Dyson HP04 power button entity."""

    _attr_translation_key = "power"
    _attr_has_entity_name = True

    def __init__(
        self, infrared_emitter_entity_id: str, unique_id: str, name: str
    ) -> None:
        """Initialize the Dyson HP04 power button entity."""
        self._infrared_emitter_entity_id = infrared_emitter_entity_id

        self._attr_unique_id = f"{unique_id}_power"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=name,
        )

    @override
    async def async_press(self) -> None:
        """Send the power key press."""
        # The power key toggles the device; a press always transmits it.
        await self._async_send_key(DysonHP04Code.POWER)
