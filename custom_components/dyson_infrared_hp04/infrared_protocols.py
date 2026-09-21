"""Dyson Pure (21-bit) IR protocol, copied from infrared-protocols.

This file is copied from the add-dyson-hp04 branch of
https://github.com/newAM/infrared-protocols (a fork of
https://github.com/home-assistant-libs/infrared-protocols), from
infrared_protocols/commands/__init__.py, infrared_protocols/commands/dyson.py,
and infrared_protocols/codes/dyson/hp04.py.  Upstream is MIT licensed.

The reason for the copy: the Dyson HP04 support has not yet been reviewed and
submitted as a pull request to infrared-protocols, but the integration should
be usable in the meantime.  Delete this file and depend on the
infrared-protocols package once the support is released there.
"""

import abc
from enum import IntEnum
from typing import ClassVar, override


class Command(abc.ABC):
    """Base class for IR commands."""

    modulation: int
    repeat_count: int

    def __init__(self, *, modulation: int, repeat_count: int = 0) -> None:
        """Initialize the IR command."""
        self.modulation = modulation
        self.repeat_count = repeat_count

    @abc.abstractmethod
    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the command.

        Positive values are pulse (high) durations in microseconds; negative
        values are space (low) durations in microseconds.
        """


class DysonPureCommand(Command):
    """Dyson Pure (purifier) infrared command.

    Protocol specification:
      - Header: 2200us mark, 750us space
      - Bit mark: 710us (constant)
      - Bit space: 760us = "0", 1480us = "1"
      - 21-bit payload, MSB-first: 8-bit device ID + 8-bit command + 3-bit
        checksum + 2-bit rolling counter
      - Footer: 710us mark
      - While a key is held: a repeat frame (header + a single "1" bit +
        footer) is sent every ~51ms
    """

    # Checksum recovered from OEM remote captures: bit i is the parity of
    # the command under mask i, XORed into the low three bits of the device
    # ID shifted right by two.
    _CHECKSUM_MASKS: ClassVar[tuple[int, ...]] = (
        0b10101110,
        0b11010110,
        0b01101010,
    )

    device_id: int
    command: int
    counter: int

    def __init__(
        self,
        *,
        device_id: int,
        command: int,
        counter: int = 0,
        modulation: int = 38000,
        repeat_count: int = 0,
    ) -> None:
        """Initialize a Dyson Pure command.

        Args:
            device_id: 8-bit device identifier (0x08 for the HP04).
            command: 8-bit command code.
            counter: 2-bit rolling counter; observed to advance by one on
                consecutive presses of the same key.
            modulation: Carrier frequency in Hz.
            repeat_count: Number of hold repeat frames to append.

        """
        super().__init__(modulation=modulation, repeat_count=repeat_count)
        if not 0 <= device_id <= 0xFF:
            raise ValueError(
                f"device ID must be an 8-bit value (0-0xFF), got {device_id:#x}"
            )
        if not 0 <= command <= 0xFF:
            raise ValueError(
                f"command must be an 8-bit value (0-0xFF), got {command:#x}"
            )
        if not 0 <= counter <= 0b11:
            raise ValueError(f"counter must be a 2-bit value (0-3), got {counter}")
        self.device_id = device_id
        self.command = command
        self.counter = counter

    @staticmethod
    def _checksum(device_id: int, command: int) -> int:
        """Compute the 3-bit checksum of a device ID and command byte."""
        checksum = (device_id >> 2) & 0b111
        for index, mask in enumerate(DysonPureCommand._CHECKSUM_MASKS):
            checksum ^= ((command & mask).bit_count() & 1) << (2 - index)
        return checksum

    @override
    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the Dyson Pure command."""
        header_mark = 2200
        header_space = 750
        bit_mark = 710
        zero_space = 760
        one_space = 1480
        repeat_gap = 51000

        payload = (
            (self.device_id << 13)
            | (self.command << 5)
            | (self._checksum(self.device_id, self.command) << 2)
            | self.counter
        )

        timings: list[int] = [header_mark, -header_space]

        # 21 bits, MSB-first
        for i in range(20, -1, -1):
            bit = (payload >> i) & 1
            timings.append(bit_mark)
            timings.append(-(one_space if bit else zero_space))

        timings.append(bit_mark)

        # Hold repeat frames: header + a single "1" bit + footer.
        for _ in range(self.repeat_count):
            timings.extend(
                [
                    -repeat_gap,
                    header_mark,
                    -header_space,
                    bit_mark,
                    -one_space,
                    bit_mark,
                ]
            )

        return timings


DYSON_HP04_DEVICE_ID = 0x08


class DysonHP04Code(IntEnum):
    """Dyson HP04 IR command codes."""

    POWER = 0x80
    INFO = 0xDB
    FAN_UP = 0xAB
    FAN_DOWN = 0xAC
    HEAT_UP = 0xBD
    HEAT_DOWN = 0xBF
    AUTO = 0xD4
    COOL = 0xB2
    OSCILLATE = 0x99
    AIRFLOW_DIRECTION = 0xC2
    TIMER = 0x9C
    NIGHT = 0xC8
