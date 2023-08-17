# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
TC2290-DT Reverse engineering trainer
"""
import logging
from binascii import unhexlify
from difflib import SequenceMatcher
from time import sleep
from typing import Callable, Optional

import hid

from tc2290.protocol import Address, Command, Chunk, Data, Header, Message
from tc2290.surface import Surface


class TC2290:
    _VENDOR_ID = 4640  # tc-electronic
    _PRODUCT_ID = 113  # TC 2290

    _logging: logging
    _device: hid.device
    _receive_callback: Callable[[list], None]

    surface: Surface

    def __init__(self, receive_callback: Optional[Callable[[list], None]] = None) -> None:
        self._logging = logging.getLogger()
        self._logging.setLevel(logging.DEBUG)  # FIXME: remove for production

        self._receive_callback = receive_callback

        self._device = hid.device()
        self._device.open(self._VENDOR_ID, self._PRODUCT_ID)
        self._device.set_nonblocking(True)  # Allows polling in an infinite loop

        self.surface = Surface()

    def __del__(self) -> None:
        self.send(Message(Header(Command.INSTANCE_STOP)))
        self._device.close()

    def _read(self) -> list | None:
        data = self._device.read(Message.MAX_SIZE)
        if data:
            logging.debug(f"<- {bytes(data).hex(' ')}")
            # TODO: update local model
        return data

    def _write(self, data: list) -> None:
        # TODO: update local model
        self._device.write(data)

    def poll(self) -> None:
        data = self._read()
        if data:
            logging.debug(f"<- {bytes(data).hex(' ')}")
            if self._receive_callback:
                self._receive_callback(data)

    def send(self, data: Message) -> None:
        logging.debug(f"-> {bytes(data).hex(' ')}")
        self._write([0x00, *data])

    def sendline(self, line: str) -> None:
        size = int(len(line) / 2)  # Hex representation uses 2 characters per byte
        if size > Message.MAX_SIZE:
            raise ValueError(f'Line is too long: {size} > {Message.MAX_SIZE}')
        del size
        self.send(Message(list(unhexlify(line))))

    def wakeup(self) -> None:
        self.send(Message(Header(Command.INSTANCE_START)))

    @staticmethod
    def address(data: list) -> str:
        address = None
        byte = 8  # Byte 8 contains the button ID (With a reply starting by 0c 08 00 00 01 00 00 00)
        try:
            address = Address(data[byte]).name
        except ValueError:
            pass
        return address

    def all(self) -> None:
        """
        Illuminates all controls
        """
        for addr in range(
                Address(0x4B),  # We skip the first element which is brightness
                Address(0x6D),
                Data.MAX_CHUNKS,
        ):
            header = Header(Command.WRITE_REG, address=addr)
            data = Data([Chunk([0xFF] * Chunk.SIZE)] * Data.MAX_CHUNKS)
            message = Message(header, data)
            self.send(message)

    def fw_ver(self) -> str:
        # FIXME: separate query from reply
        self._device.set_nonblocking(False)
        self.send(Message(Header(Command.READ_REG, address=0x02)))
        version = bytes(self._read())[Header.SIZE:-1].decode('ASCII').rstrip('\x00')
        self._device.set_nonblocking(True)
        return version

    def instance(self, instance_name='', instance_id=1):
        instance = instance_name.encode()
        assert (len(instance) < 43)
        message = Message(
            header=Header(
                Command.INSTANCE_START,
                data_size=len(instance),
                instance=instance_id,
            ),
            data=Data(data=list(instance)),
        )
        self.send(message)


class CallbackManager:
    def __init__(self) -> None:
        self.previous_data = []

    @staticmethod
    def _hex(data: list) -> str:
        return bytes(data).hex(' ')

    def print(self, data: list) -> None:
        # print(self._hex(data))
        # print(bytes(data).decode('ASCII', errors='ignore'))  # Nothing interesting
        print(TC2290.address(data))  # Button name mapping
        a = self.previous_data
        b = data
        m = SequenceMatcher(a=a, b=b, autojunk=False)
        print(m.ratio())
        print(f'Matching: {m.find_longest_match()}')
        self.previous_data = data


def main():
    tc = TC2290(receive_callback=CallbackManager().print)
    print(tc.fw_ver())
    tc.wakeup()
    tc.all()
    while True:
        tc.poll()


if __name__ == '__main__':
    main()
