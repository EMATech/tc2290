TC2290-DT
=========

Reverse Engineering
-------------------

# 2022-11-19

## External features

Casing:
- Plastic (Main body)
- Aluminium (Front panel)
- Steel (Stand/weight)

Electronics:
- Micro USB Type B socket
- 3× 2 digits red 7-segment displays
- 1× 4 digits red 7-segment displays
- 71 LEDs of various colors
    - 2 × 11 × 2 Metering
    - 15 + 12 status
- 35 very small tactile buttons

## Disassembly

Done.
Nothing fascinating.
Casing is mostly plastic in which self-tapping screws are used:
- 4 hex size 2 on the front panel
- 3 philips 0 securing the main board
- Didn't bother removing the Philips screw on the back that retain the USB connector and associated shielding and the
steel baseplate
- The back also features 2 threaded inserts (Size?) for mounting into the TC ICON Dock is suppose.

TODO: add photos

## USB device

- VID: `0x1220` (TC Electronic)
- PID: `0x0071` (Unknown)

TODO: add PID to USB IDs database

Reports:

- USB 1.1
- Self-powered
- 100mA
- 2 endpoints

### HID compliant

- VID: `4640` (TC Group)
- PID: `113` (TC2290)

PACKET SIZE: `64` bytes

### Capture & analysis

[USBpcap (Wireshark) Capture](capture/2022-11-19%20TC2290-DT.pcapng)

- -> `[0]*64` Reset ?
- (No reply)
- -> `[0x00, 0x01,0x2D, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00] + 43 bytes Instance name (see below) + byte[52]=0x01`
  Handshake?
- <- Echoes the handshake with `byte[52]=0x02 and byte[53]=0x01`
- -> `[0x00, 0x01,0x2D, 0x00, 0x00, 0x02]` ?
- <- Also echoed
- -> `[0x00, 0x01,0x2D, 0x00, 0x00, 0x03]`
- <- Sends previous reply (`0x02` echo)

`[0x00, 0x0F, 0x38, 0x00, 0x02, 0x01]` Seem to be the firmware version request
The reply is the version number in ASCII (`1.0.0.4-358`).
Doesn't work on isolation though.
May need the handshake first.

A message is emitted on button down and button release.

It generally starts with `0c 08 00 00 ff ff ff ff`

Byte 8 (#9) is the button ID.

- 110 (0x6E): MODULATION - SPEED - UP
- 110: MODULATION - SPEED - DOWN
- 112: MODULATION - DEPTH - UP
- 113: MODULATION - DEPTH - DOWN
- 114: MODULATION - WAVE FORM
- 115: MODULATION - SELECT
- 116: PAN - MOD
- 117: DYN - MOD
- 118: PAN-DYN DIRECT
- 119: PAN-DYN REVERSE
- 120: DELAY - UP
  [...]
- 144 (0x90): KEYBOARD - ENTER

Followed by `00 00 00`.

12 bytes.

Followed by 52 bytes of gibberish for now (Always changing data).

No byte seem to encode the state (Down or release) on its own.

Looking at the capture, the 6 first bytes seem special in the host->device direction and the 10 first bytes in the
device->host direction.
43 bytes (#8 to #51) contain the first 43 characters of the instance name.
It is registered in the device using the "01 2D 00 00 01 00 00 00" command followed by the 43 bytes of instance name.
Byte 53 is 01 in the request and 02 in the reply.

There is some sort of internal buffer managing instances.
The plugin keeps sending update messages with the first instance name even when the second is up and also appears in
messages.
This seems to help plugin instances to know which one is active.
The name of the active instance displayed by the inactive instance is truncated at the same 43 character length.
Using Unicode characters, they are byte truncated at the same 43 boundary (Displaying only 21 characters for 2-byte
chars.)
I think that the device literally doesn't care and just spits out this data whenever the other instance requests it
or is just used internally
as a 43 bytes ID.
What an odd choice of length...


## Trainer program

- Connects to the device
- Polls data from it
  - Spits out raw messages
  - Interpret button presses
