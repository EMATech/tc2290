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
- -> `[0x01,0x2D, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00] + 43 bytes Instance name (see below) + byte[52]=0x01`
  Handshake?
- <- Echoes the handshake with `byte[52]=0x02 and byte[53]=0x01`
- -> `[0x01,0x2D, 0x00, 0x00, 0x02]` ?
- <- Also echoed
- -> `[0x01,0x2D, 0x00, 0x00, 0x03]`
- <- Sends previous reply (`0x02` echo)

`[0x0F, 0x38, 0x00, 0x02, 0x01]` Seem to be the firmware version request
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

Python with hidapi.

- Connects to the device
- Polls data from it
  - Spits out raw messages
  - Interpret button presses


# 2022-11-20

012d000001000000556e6e616d65642028496e7374616e63652023312900000000000000

Wakes the device up

1138004f0100000000000000010000003f00000066000000010000000100000001000000

Updates the Modulation display

1138005d010000004f0000005b0000003f00000006000000010000000000000000000000

Updates the Delay display

110c006b0100000000000000010000000100000006000000010000000000000000000000

Updates the Preset status leds


## Display format


### Header

| 11      | 38    | 00  | 5d                     | 01        | 00  | 00  | 00  |
|---------|-------|-----|------------------------|-----------|-----|-----|-----|
| Command | Size? |     | Start Address (Offset) | Instance? |     |     |     |


### Data 

| 4f                | 00  | 00  | 00  | 5b                | 00  | 00  | 00  | 3f                | 00  | 00  | 00  | 06                | 00  | 00  | 00  | 01        | 00  | 00  | 00  | 00      | 00  | 00  | 00  | 00       | 00  | 00  | 00  |
|-------------------|-----|-----|-----|-------------------|-----|-----|-----|-------------------|-----|-----|-----|-------------------|-----|-----|-----|-----------|-----|-----|-----|---------|-----|-----|-----|----------|-----|-----|-----|
| DELAY #4 segments |     |     |     | DELAY #3 segments |     |     |     | DELAY #2 segments |     |     |     | DELAY #1 segments |     |     |     | DELAY LED |     |     |     | MOD LED |     |     |     | SYNC LED |     |     |     |


| 01                   | 00  | 00  | 00  | FF                   | 00  | 00  | 00  | 07                    | 00  | 00  | 00  | 01         | 00  | 00  | 00  | 01                  |
|----------------------|-----|-----|-----|----------------------|-----|-----|-----|-----------------------|-----|-----|-----|------------|-----|-----|-----|---------------------|
| FEEDBACK #1 segments |     |     |     | FEEDBACK #2 segments |     |     |     | FEEDBACK display LEDs |     |     |     | F BACK LED |     |     |     | FEEDBACK F BACK LED |

### Addresses

The delimiters denote blocks that work together.
A message not sent in sequence will reset all the elements that follow in that block. 

- 0x00-0x39: ???
- ---
- 0x40-0x49: ???
- 0x4A: Brightness (00: Full, 0F: Dim)
- 0x4B: INPUT L LEDs bitmap
- 0x4C: INPUT R LEDs bitmap
- 0x4D: OUTPUT L LEDs bitmap
- 0x4E: OUTPUT R LEDs bitmap
- 0x4F: MODULATION OSC / THRESHOLD LED
- 0x50: MODULATION RED LED LEFT OF DISPLAY
- 0x51: MODULATION 7-segment Right digit (#2)
- 0x52: MODULATION 7-segment Left digit (#1)
- 0x53: MODULATION RED LEDs bitmap Right of display first col
- 0x54: MODULATION RED LEDs bitmap Right of display second col
- 0x55: MODULATION SPEED LED
- 0x56: MODULATION DEPTH LED
- 0x57: PAN-DYN PAN MOD LED
- 0x58: PAN-DYN DYN MOD LED
- 0x59: PAN-DYN DELAY LED
- --
- 0x5A: PAN-DYN DIRECT LED
- 0x5B: PAN-DYN REVERSE LED
- 0x5C: DELAY TIME LED
- 0x5D: DELAY 7-segment leftmost digit (#4)
- 0x5E: DELAY 7-segment center-left digit (#3)
- 0x5F: DELAY 7-segment center-right digit (#2)
- 0x60: DELAY 7-segment rightmost digit (#1)
- 0x61: DELAY DELAY LED
- 0x62: DELAY MOD LED
- 0x63: DELAY SYNC LED
- 0x64: FEEDBACK 7-segment Right digit (#2)
- 0x65: FEEDBACK 7-segment Left digit (#1)
- 0x66: FEEDBACK RED LEDs bitmap right of display
- 0x67: FEEDBACK F BACK LED
- --
- 0x68: FEEDBACK INV LED
- 0x69: PRESET SPEC 7-segment Right digit (#2)
- 0x6A: PRESET SPEC 7-segment Left digit (#1)
- 0x6B: PRESET SPEC RED LEDs bitmap right of display
- 0x6C: PRESET SPEC PRESET LED
- 0x6D: PRESET SPEC DELAY ON LED
- ---
- 0x6E-0xFF: ???


### Data

32 bits 

Sent in 4 bytes little-endian (LSB first)

# 2022-11-24

The reset per block was because I always used the maximum size for the message.
When sized appropriately we can update a single element without disrupting the rest.

# 2022-11-25

- USB VID: `0x0073` = TC 8210
