"""Shared entity base for Dyson HP04 infrared entities."""

from infrared_protocols.codes.dyson.hp04 import DYSON_HP04_DEVICE_ID, DysonHP04Code
from infrared_protocols.commands.dyson import DysonPureCommand

from homeassistant.components.infrared import InfraredEmitterConsumerEntity

# A key press on the OEM remote transmits the command frame followed by two
# hold repeat frames.
HOLD_REPEAT_COUNT = 2


class DysonInfraredHP04Entity(InfraredEmitterConsumerEntity):
    """Base class for entities that transmit HP04 key presses."""

    # The remote cycles a 2-bit rolling counter so consecutive presses of
    # the same key are not identical frames.
    _counter = 0

    async def _async_send_key(self, code: DysonHP04Code) -> None:
        """Transmit one HP04 key press through the infrared emitter."""
        command = DysonPureCommand(
            device_id=DYSON_HP04_DEVICE_ID,
            command=code.value,
            counter=self._counter,
            repeat_count=HOLD_REPEAT_COUNT,
        )
        await self._send_command(command)
        self._counter = (self._counter + 1) & 0b11
