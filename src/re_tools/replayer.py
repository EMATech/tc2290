"""
How to use:
From wireshark export to text
grep only "HID Data" messages
Profit!
"""

import logging
from binascii import unhexlify

from tc2290 import TC2290

logging.basicConfig(level=logging.INFO)

tc = TC2290()

with open('../../capture/ORIG_HID.txt') as f:
    for line in f:
        data = list(unhexlify(line[10:-4]))  # Omit HID Data: and weird chars after the data
        input()
        tc.send(data)
        logging.info(line)
