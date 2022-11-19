# Copyright 2022 Raphaël Doursenaud

"""
TC2290-DT Reverse engineering trainer
"""
from binascii import hexlify
from difflib import SequenceMatcher
from enum import IntEnum

import hid


class TCButtons(IntEnum):
    """
    Buttons are arrange by function groups from left to right in a sensible manner.
    """
    MODULATION_SPEED_UP = 0x6E
    MODULATION_SPEED_DOWN = 0x6F
    MODULATION_DEPTH_UP = 0x70
    MODULATION_DEPTH_DOWN = 0x71
    MODULATION_WAVE_FORM = 0x72
    MODULATION_SELECT = 0x73
    PAN_MOD = 0x74
    DYN_MOD = 0x75
    PAN_DYN_DELAY_DIRECT = 0x76
    PAN_DYN_REVERSE = 0x77
    DELAY_UP = 0x78
    DELAY_DOWN = 0x79
    DELAY_MOD = 0x7A
    DELAY_SYNC = 0x7B
    DELAY_LEARN = 0x7C
    FEEDBACK_UP = 0x7D
    FEEDBACK_DOWN = 0x7E
    FEEDBACK_INV = 0x7F
    FEEDBACK_SELECT = 0x80
    PRESET_SPEC_UP = 0x81
    PRESET_SPEC_DOWN = 0x82
    PRESET_SPEC_DELAY = 0x83
    PRESET_SPEC_SPEC = 0x84
    KEYBOARD_7 = 0x85
    KEYBOARD_8 = 0x86
    KEYBOARD_9 = 0x87
    KEYBOARD_4 = 0x88
    KEYBOARD_5 = 0x89
    KEYBOARD_6 = 0x8A
    KEYBOARD_1 = 0x8B
    KEYBOARD_2 = 0x8C
    KEYBOARD_3 = 0x8D
    KEYBOARD_0 = 0x8E
    KEYBOARD_DOT = 0x8F
    KEYBOARD_ENTER = 0x90


class TC:
    _VID = 4640
    _PID = 113
    _DATA_SIZE = 64

    def __init__(self):
        self._device = hid.device()
        self._device.open(self._VID, self._PID)
        self._device.set_nonblocking(True)  # Allows polling in an infinite loop

    def __del__(self):
        self._device.close()

    def _read(self):
        return self._device.read(self._DATA_SIZE)

    def _write(self, data):
        self._device.write([0x00].append(data))

    def poll(self):
        data = self._read()
        if data:
            return data

    @staticmethod
    def button(data):
        button = None
        byte = 8  # Byte 8 contains the button ID (With a reply starting by 0c 08 00 00 ff ff ff ff)
        try:
            button = TCButtons(data[byte]).name
        except ValueError:
            pass
        return button


class Callback:
    def __init__(self):
        self.previous_data = []

    @staticmethod
    def _hex(data):
        return hexlify(bytes(data), ' ')

    def print(self, data):
        print(self._hex(data))
        # print(bytes(data).decode('ASCII', errors='ignore'))  # Nothing interesting
        print(TC.button(data))  # Button name mapping
        a = self._hex(self.previous_data)
        b = self._hex(data)
        m = SequenceMatcher(a=a, b=b, autojunk=False)
        print(m.ratio())
        print(f'Matching: {m.find_longest_match()}')
        self.previous_data = data


def main():
    tc = TC()
    callback = Callback()
    while True:
        data = tc.poll()
        if data:
            callback.print(data)


if __name__ == '__main__':
    main()
