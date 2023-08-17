# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
TC2290-DT Reverse engineered protocol
"""
from dataclasses import dataclass, field
from enum import unique, IntEnum
from typing import Sequence


@unique
class Address(IntEnum):
    # 0x01..0x49: ???
    INIT = 0x00
    VERSION = 0x02

    # Settings
    GLOBAL__BRIGHTNESS = 0X4A  # 00: FULL, 0F: DIM

    # Outputs (Leds)
    INPUT__LEDS_L = 0X4B
    INPUT__LEDS_R = 0X4C
    OUTPUT__LEDS_L = 0X4D
    OUTPUT__LEDS_R = 0X4E
    MODULATION__LED_OSC_THRESHOLD = 0X4F
    MODULATION__LED_DISPLAY_LEFT = 0X50
    MODULATION__DIGIT_2 = 0X51
    MODULATION__DIGIT_1 = 0X52
    MODULATION__LEDS_WAVE_FORM = 0X53
    MODULATION__LEDS_SELECT = 0X54
    MODULATION__LED_SPEED = 0X55
    MODULATION__LED_DEPTH = 0X56
    PAN_DYN__LED_PAN_MOD = 0X57
    PAN_DYN__LED_DYN_MOD = 0X58
    PAN_DYN__LED_DELAY = 0X59
    PAN_DYN__LED_DIRECT = 0X5A
    PAN_DYN__LED_REVERSE = 0X5B
    DELAY__LED_TIME = 0X5C
    DELAY__DIGIT_4 = 0X5D
    DELAY__DIGIT_3 = 0X5E
    DELAY__DIGIT_2 = 0X5F
    DELAY__DIGIT_1 = 0X60
    DELAY__LED_DELAY_ON = 0X61
    DELAY__LED_MOD = 0X62
    DELAY__LED_SYNC = 0X63
    FEEDBACK__DIGIT_2 = 0X64
    FEEDBACK__DIGIT_1 = 0X65
    FEEDBACK__LEDS_SELECT = 0X66
    FEEDBACK__LED_F_BACK = 0X67
    FEEDBACK__LED_INV = 0X68
    PRESET_SPEC__DIGIT_2 = 0X69
    PRESET_SPEC__DIGIT_1 = 0X6A
    PRESET_SPEC__LEDS_MIX_SPEC = 0X6B
    PRESET_SPEC__LED_PRESET = 0X6C
    PRESET_SPEC__LED_DELAY_ON = 0X6D

    # Inputs (Buttons)
    MODULATION__SPEED_UP = 0x6E
    MODULATION__SPEED_DOWN = 0x6F
    MODULATION__DEPTH_UP = 0x70
    MODULATION__DEPTH_DOWN = 0x71
    MODULATION__WAVE_FORM = 0x72
    MODULATION__SELECT = 0x73
    PAN_DYN__PAN_MOD = 0x74
    PAN_DYN__DYN_MOD = 0x75
    PAN_DYN__DELAY_DIRECT = 0x76
    PAN_DYN__REVERSE = 0x77
    DELAY__UP = 0x78
    DELAY__DOWN = 0x79
    DELAY__MOD = 0x7A
    DELAY__SYNC = 0x7B
    DELAY__LEARN = 0x7C
    FEEDBACK__UP = 0x7D
    FEEDBACK__DOWN = 0x7E
    FEEDBACK__INV = 0x7F
    FEEDBACK__SELECT = 0x80
    PRESET_SPEC__PRESET_UP = 0x81
    PRESET_SPEC__PRESET_DOWN = 0x82
    PRESET_SPEC__DELAY = 0x83
    PRESET_SPEC__MIX_SPEC = 0x84
    KEYBOARD__7 = 0x85
    KEYBOARD__8 = 0x86
    KEYBOARD__9 = 0x87
    KEYBOARD__4 = 0x88
    KEYBOARD__5 = 0x89
    KEYBOARD__6 = 0x8A
    KEYBOARD__1 = 0x8B
    KEYBOARD__2 = 0x8C
    KEYBOARD__3 = 0x8D
    KEYBOARD__0 = 0x8E
    KEYBOARD__DOT = 0x8F
    KEYBOARD__ENTER = 0x90

    # 0x91..0xFF: ???


@unique
class Command(IntEnum):
    INIT = 0x00  # TODO. No data. No Addr.
    INSTANCE_START = 0x01  # Len: 2D. Data: instance name. Addr: 00. Instance: 01
    INSTANCE_RENAME = 0x0A  # TODO. Len: . Data: instance name. Addr: 00, 01, 02 or 03
    INSTANCE_STOP = 0x0B  # No data
    INSTANCE_FOCUS = 0x0D  # TODO. Or is it ping? No data. Addr 00, 01, 02 or 03
    REPLY = 0x0C  # In replies only
    WRITE_REG = 0x11  # Len: any. Data: Leds. Addr: Address. Instance: 01
    READ_REG = 0x0F  # Len: any. Data: Buttons. Addr: Address. Instance: 01


class ChunkDataDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner) -> list[int]:
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value: int | list[int]):
        # Allow single int
        if isinstance(value, int):
            value = [value]
        # Check type
        if not isinstance(value, list):
            raise TypeError("data should be a list of ints or a single int")
        for v in value:
            if not isinstance(v, int):
                TypeError("the list should only contain ints")
        # Pad data
        length = len(value)
        if length < Chunk.SIZE:
            for _ in range(Chunk.SIZE - length):
                value.append(0x00)
        # Set
        setattr(instance, self._name, value)


@dataclass
class Chunk(Sequence):
    SIZE = 4

    data: list[int] | int = ChunkDataDescriptor(default=0x00)

    def __len__(self) -> int:
        return self.SIZE

    def __getitem__(self, item) -> int:
        if item >= self.SIZE:
            raise IndexError("index out of range")
        return self.data[item]


class DataDescriptor:
    def __init__(self, *, default_factory):
        self._default_factory = default_factory

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default_factory

        return getattr(instance, self._name, self._default_factory)

    def __set__(self, instance, value: int | Chunk | list[int] | list[Chunk] | None):
        # Default to padding with zeroes
        if value is list:
            value = [0x00] * Data.MAX_SIZE
        # Allow single int or single Chunk()
        if isinstance(value, int) or isinstance(value, Chunk):
            value = [value]
        # Allow list of ints
        if isinstance(value, list):
            length = len(value)
            if length:
                if isinstance(value[0], int):
                    if length > Data.MAX_SIZE:
                        raise ValueError(f"data list size should not exceed {Data.MAX_SIZE}")
                    if length <= Chunk.SIZE:
                        value = [Chunk(value)]
                    else:
                        new_value = []
                        for i in range(0, length, Chunk.SIZE):
                            new_value.append(Chunk(value[i:i + Chunk.SIZE]))
                        value = new_value
            length = len(value)
            if length:
                if isinstance(value[0], Chunk):
                    if length > Data.MAX_CHUNKS:
                        raise ValueError(f"data size should not exceed {Data.MAX_CHUNKS}")
        # Check type
        if not isinstance(value, list):
            raise TypeError("data should be a list of Chunk(), a single Chunk(), a list of ints or a single int")
        for v in value:
            if not isinstance(v, Chunk):
                raise TypeError("data should be a list of MessageDataChunk")
        # Set
        setattr(instance, self._name, value)


@dataclass
class Data(Sequence):
    MAX_SIZE = 56
    MAX_CHUNKS = int(MAX_SIZE / Chunk.SIZE)

    data: [Chunk] = DataDescriptor(default_factory=Chunk)

    def __len__(self) -> int:
        return len(self.data) * Chunk.SIZE

    def __getitem__(self, item) -> int:
        if item >= len(self.data):
            raise IndexError("index out of range")
        return self.data[item]


class DataSizeDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value: int | None):
        if value:  # Allow None
            if value % Chunk.SIZE:
                raise ValueError(f"data size must be a multiple of {Chunk.SIZE}")
            value = int(value)
        setattr(instance, self._name, value)


class CommandDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value):
        if isinstance(value, int):
            value = Command(value)
        if isinstance(value, str):
            value = Command[value]
        if not isinstance(value, Command):
            raise TypeError("command must be a Command()")
        setattr(instance, self._name, int(value))


class AddressDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value):
        if isinstance(value, int):
            value = Address(value)
        if isinstance(value, str):
            value = Address[value]
        if not isinstance(value, Address):
            raise TypeError("address must be an Address()")
        setattr(instance, self._name, int(value))


@dataclass
class Header(Sequence):
    """
    Header message

    Format: <command> <data size> 00 <address> <instance> 00 00 00
    """
    SIZE = 8

    command: Command | int = CommandDescriptor(default=None)
    data_size: int = DataSizeDescriptor(default=None)
    address: Address | int | str = AddressDescriptor(default=0x00)
    instance: int = 0x01

    def __len__(self) -> int:
        return self.SIZE

    def __getitem__(self, item) -> int:
        if item >= self.SIZE:
            raise IndexError("index out of range")
        if item == 0:
            return self.command
        elif item == 1:
            return self.data_size
        elif item == 3:
            return self.address
        elif item == 4:
            return self.instance
        else:
            return 0x00

    def __str__(self) -> str:
        value = ''
        for i in range(self.SIZE):
            value += f'{self[i]:02X}'
        return value


class MessageHeaderDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value: int | list[int] | Chunk | list[Chunk] | Header):
        if not isinstance(value, Header):
            value = Header(value)
        if not Header.data_size:
            Header.data_size = Message.MAX_SIZE
        setattr(instance, self._name, value)


class MessageDataDescriptor:
    def __init__(self, *, default_factory):
        self._default_factory = default_factory

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default_factory

        return getattr(instance, self._name, self._default_factory)

    def __set__(self, instance, value: int | list[int] | Chunk | list[Chunk] | Data):
        if not isinstance(value, Data):
            value = Data(value)
        # Set appropriate data size in header
        instance: Message
        instance.header.data_size = len(value)
        setattr(instance, self._name, value)


@dataclass
class Message(Sequence):
    MAX_SIZE = 64

    header: Header = MessageHeaderDescriptor(default=None)
    data: Data = MessageDataDescriptor(default_factory=list)

    def __len__(self) -> int:
        return len(self.header) + len(self.data)

    def __getitem__(self, item) -> int:
        if item >= (len(self.header) + len(self.data)):
            raise IndexError("index out of range")
        if item in range(self.header.SIZE):
            return self.header[item]
        else:
            data_index = item - self.header.SIZE
            chunk = int(data_index / 4)
            chunk_index = data_index % 4
            return self.data[chunk][chunk_index]


# Sanity checks
assert (Data.MAX_CHUNKS * Chunk.SIZE == Data.MAX_SIZE)
assert (Header.SIZE + Data.MAX_SIZE == Message.MAX_SIZE)

# TODO: decoder
