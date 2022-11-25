import itertools
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Flag, auto, Enum

from tc2290 import Address


class BrightnessStrengthDescriptor:
    def __init__(self, *, default):
        self._default = default

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self._default

        return getattr(instance, self._name, self._default)

    def __set__(self, instance, value):
        if value > Brightness.MAX:
            raise ValueError(f"brightness strength can't be more than {Brightness.MAX}")
        setattr(instance, self._name, int(value))


@dataclass
class Brightness:
    MAX = 255

    strength: int = BrightnessStrengthDescriptor(default=0)
    address: Address = Address.GLOBAL__BRIGHTNESS

    @property
    def value(self):
        return self.strength ^ self.MAX

    @value.setter
    def value(self, value):
        self.strength = value ^ self.MAX


class LedColor(Flag):
    GREEN = auto()
    YELLOW = auto()
    RED = auto()


@dataclass
class Led:
    color: LedColor = LedColor.RED
    state: bool = False
    address: Address | None = None

    def toggle(self):
        self.state = not self.state

    def on(self):
        self.state = True

    def off(self):
        self.state = False


@dataclass
class Button:
    state: bool = False
    address: Address | None = None


class LedMap:
    leds: list[Led]
    address: Address

    def __init__(self, size: int, address: Address = None):
        if size not in (2, 3, 4, Digit.SIZE, BarGraph.SIZE):
            raise ValueError
        self.leds = []
        for _ in range(size):
            self.leds.append(Led())
        self.address = address


class MeterDirection(Enum):
    INPUT = auto()
    OUTPUT = auto()


class MeterSide(Enum):
    L = auto()
    R = auto()


class BarGraph(LedMap):
    _SIZE_GREEN = 7
    _SIZE_YELLOW = 3
    _SIZE_RED = 1
    SIZE = _SIZE_GREEN + _SIZE_YELLOW + _SIZE_RED

    direction: MeterDirection
    side: MeterSide

    minus_60: Led
    minus_50: Led
    minus_40: Led
    minus_30: Led
    minus_24: Led
    minus_18: Led
    minus_12: Led
    minus_9: Led
    minus_6: Led
    minus_3: Led
    zero: Led

    def __init__(self, direction: MeterDirection, side: MeterSide, address: Address):
        self.direction = direction
        self.side = side
        super().__init__(self.SIZE, address)
        for i in range(0, self.SIZE):
            for _ in range(0, self._SIZE_GREEN):
                self.leds[i].color = LedColor.GREEN
            for _ in range(0, self._SIZE_YELLOW):
                self.leds[i].color = LedColor.YELLOW
            for _ in range(0, self._SIZE_RED):
                self.leds[i].color = LedColor.RED

    @property
    def minus_60(self):
        return self.leds[0]

    @property
    def minus_50(self):
        return self.leds[1]

    @property
    def minus_40(self):
        return self.leds[2]

    @property
    def minus_30(self):
        return self.leds[3]

    @property
    def minus_24(self):
        return self.leds[4]

    @property
    def minus_18(self):
        return self.leds[5]

    @property
    def minus_12(self):
        return self.leds[6]

    @property
    def minus_9(self):
        return self.leds[7]

    @property
    def minus_6(self):
        return self.leds[8]

    @property
    def minus_3(self):
        return self.leds[9]

    @property
    def zero(self):
        return self.leds[10]


class StereoBarGraph:
    left: BarGraph
    right: BarGraph

    def __init__(self, direction: MeterDirection, address_left: Address, address_right: Address):
        self.left = BarGraph(direction=direction, side=MeterSide.L, address=address_left)
        self.right = BarGraph(direction=direction, side=MeterSide.R, address=address_right)


class SevenSegmentFont:
    _SEVEN_SEGMENT_FONT = {
        # Format: a, b, c, d, e, f
        0: (True, True, True, True, True, True, False),
        1: (False, True, True, False, False, False, False),
        2: (True, True, False, True, True, False, True),
        3: (True, True, True, True, False, False, True),
        4: (False, True, True, False, False, True, True),
        5: (True, False, True, True, False, True, True),
        6: (True, False, True, True, True, True, True),
        7: (True, True, True, False, False, False, False),
        8: (True, True, True, True, True, True, True),
        9: (True, True, True, True, False, True, True),
        0xA: (True, True, True, False, True, True, True),
        0xB: (False, False, True, True, True, True, True),
        0xC: (True, False, False, True, True, True, False),
        0xD: (False, True, True, True, True, False, True),
        0xE: (True, False, False, True, True, True, True),
        0xF: (True, False, False, False, True, True, True),
    }

    # Support numbers from string
    for i in range(0, 0x10):
        _SEVEN_SEGMENT_FONT[f'{i:X}'] = _SEVEN_SEGMENT_FONT[i]

    def __len__(self):
        return len(self._SEVEN_SEGMENT_FONT)

    def __getitem__(self, item):
        return self._SEVEN_SEGMENT_FONT[item]

    def items(self):
        return self._SEVEN_SEGMENT_FONT.items()

    @classmethod
    def key_from_state(cls, state: tuple, class_filter: int | str = int) -> int | str | None:
        for key, font_state in cls._SEVEN_SEGMENT_FONT.items():
            if isinstance(key, class_filter) and font_state == state:
                return key
        if class_filter == str:
            return ''
        return None


class Digit(LedMap):
    _SEGMENTS = 7
    _DOT = 1
    SIZE = _SEGMENTS + _DOT

    a: Led  # Top
    b: Led  # Right, top
    c: Led  # Right, bottom
    d: Led  # Bottom
    e: Led  # Left, bottom
    f: Led  # Left, top
    g: Led  # Center
    dot: Led

    def __init__(self, address: Address = None):
        super().__init__(self.SIZE, address)

    @property
    def a(self):
        return self.leds[0]

    @property
    def b(self):
        return self.leds[1]

    @property
    def c(self):
        return self.leds[2]

    @property
    def d(self):
        return self.leds[3]

    @property
    def e(self):
        return self.leds[4]

    @property
    def f(self):
        return self.leds[5]

    @property
    def g(self):
        return self.leds[6]

    @property
    def dot(self):
        return self.leds[7]

    def from_int(self, value: int):
        if not isinstance(value, int):
            raise TypeError("not an int")
        digit = SevenSegmentFont()[value]
        for i, segment in enumerate(digit):
            self.leds[i].state = segment

    def from_str(self, value: str):
        dot = False
        if not isinstance(value, str):
            raise TypeError("not a string")
        if len(value) > 1:
            if value[1] != '.' or len(value) > 2:
                raise ValueError("only support one character or two with the second being a dot")
            if value[1] == '.':
                value = value[0]
                dot = True
        if ord(value) not in itertools.chain(range(ord('0'), ord('9')), range(ord('A'), ord('F'))):
            raise ValueError("character not supported")
        digit = SevenSegmentFont()[value]
        for i, segment in enumerate(digit):
            self.leds[i].state = segment
        self.dot.state = dot

    def _segments_state(self) -> tuple:
        return (
            self.a.state,
            self.b.state,
            self.c.state,
            self.d.state,
            self.e.state,
            self.f.state,
            self.g.state,
        )

    def to_int(self) -> int | None:
        current_state = self._segments_state()
        return SevenSegmentFont.key_from_state(current_state, int)

    def to_str(self) -> str:
        current_state = self._segments_state()
        value = SevenSegmentFont.key_from_state(current_state, str)
        if self.dot.state:
            value += '.'
        return value


class Display:
    digits: list[Digit]

    def __init__(self, size: int):
        if size not in (2, 4):
            raise ValueError
        self.digits = []
        for _ in range(size):
            self.digits.append(Digit())


# ---


class Meters:
    input: StereoBarGraph
    output: StereoBarGraph

    def __init__(self):
        self.input = StereoBarGraph(direction=MeterDirection.INPUT,
                                    address_left=Address.INPUT__LEDS_L,
                                    address_right=Address.INPUT__LEDS_R)
        self.output = StereoBarGraph(direction=MeterDirection.OUTPUT,
                                     address_left=Address.OUTPUT__LEDS_L,
                                     address_right=Address.OUTPUT__LEDS_R)


class Modulation:
    _DISPLAY_SIZE = 2
    _WAVE_FORM_OPTIONS = 4
    _SELECT_OPTIONS = 3

    osc_threshold: Led
    display_left: Led
    display: Display
    wave_form: LedMap
    sine: Led
    rand: Led
    env: Led
    trig: Led
    select: LedMap
    delay: Led
    pan: Led
    dyn: Led
    speed: Led
    speed_up: Button
    speed_down: Button
    depth: Led
    depth_up: Button
    depth_down: Button
    wave_form_toggle: Button
    select_toggle: Button

    def __init__(self):
        self.osc_threshold = Led(color=LedColor.YELLOW, address=Address.MODULATION__LED_OSC_THRESHOLD)
        self.display_left = Led(color=LedColor.RED, address=Address.MODULATION__LED_DISPLAY_LEFT)
        self.display = Display(self._DISPLAY_SIZE)
        self.display.digits[0].address = Address.MODULATION__DIGIT_1
        self.display.digits[1].address = Address.MODULATION__DIGIT_2
        self.wave_form = LedMap(size=self._WAVE_FORM_OPTIONS, address=Address.MODULATION__LEDS_WAVE_FORM)
        self.select = LedMap(size=self._SELECT_OPTIONS, address=Address.MODULATION__LEDS_SELECT)
        self.speed = Led(color=LedColor.GREEN, address=Address.MODULATION__LED_SPEED)
        self.speed_up = Button(address=Address.MODULATION__SPEED_UP)
        self.speed_down = Button(address=Address.MODULATION__SPEED_DOWN)
        self.depth = Led(color=LedColor.GREEN, address=Address.MODULATION__LED_DEPTH)
        self.depth_up = Button(address=Address.MODULATION__DEPTH_UP)
        self.depth_down = Button(address=Address.MODULATION__DEPTH_DOWN)
        self.wave_form_toggle = Button(address=Address.MODULATION__WAVE_FORM)
        self.select_toggle = Button(address=Address.MODULATION__SELECT)

    @property
    def sine(self):
        return self.wave_form.leds[0]

    @property
    def rand(self):
        return self.wave_form.leds[1]

    @property
    def env(self):
        return self.wave_form.leds[2]

    @property
    def trig(self):
        return self.wave_form.leds[3]

    @property
    def delay(self):
        return self.select.leds[0]

    @property
    def pan(self):
        return self.select.leds[1]

    @property
    def dyn(self):
        return self.select.leds[2]


class Pan:
    mod: Led
    mod_toggle: Button
    delay: Led
    direct: Led
    delay_direct_toggle: Button

    def __init__(self):
        self.mod = Led(color=LedColor.RED, address=Address.PAN_DYN__LED_PAN_MOD)
        self.mod_toggle = Button(address=Address.PAN_DYN__PAN_MOD)
        self.delay = Led(color=LedColor.RED, address=Address.PAN_DYN__LED_DELAY)
        self.direct = Led(color=LedColor.RED, address=Address.PAN_DYN__LED_DIRECT)
        self.delay_direct_toggle = Button(address=Address.PAN_DYN__DELAY_DIRECT)


class Dyn:
    mod: Led
    mod_toggle: Button
    reverse: Led
    reverse_toggle: Button

    def __init__(self):
        self.mod = Led(color=LedColor.RED, address=Address.PAN_DYN__LED_DYN_MOD)
        self.mod_toggle = Button(address=Address.PAN_DYN__DYN_MOD)
        self.reverse = Led(color=LedColor.RED, address=Address.PAN_DYN__LED_REVERSE)
        self.reverse_toggle = Button(address=Address.PAN_DYN__REVERSE)


class PanDyn:
    pan: Pan
    dyn: Dyn

    def __init__(self):
        self.pan = Pan()
        self.dyn = Dyn()


class Delay:
    _DISPLAY_SIZE = 4

    time: Led
    display: Display
    delay: Led
    delay_up: Button
    delay_down: Button
    mod: Led
    mod_toggle: Button
    sync: Led
    sync_toggle: Button
    learn: Button

    def __init__(self):
        self.time = Led(color=LedColor.RED, address=Address.DELAY__LED_TIME)
        self.display = Display(self._DISPLAY_SIZE)
        self.display.digits[0].address = Address.DELAY__DIGIT_1
        self.display.digits[1].address = Address.DELAY__DIGIT_2
        self.display.digits[2].address = Address.DELAY__DIGIT_3
        self.display.digits[3].address = Address.DELAY__DIGIT_4
        self.delay = Led(color=LedColor.GREEN, address=Address.DELAY__LED_DELAY_ON)
        self.delay_up = Button(address=Address.DELAY__UP)
        self.delay_down = Button(address=Address.DELAY__DOWN)
        self.mod = Led(color=LedColor.RED, address=Address.DELAY__LED_MOD)
        self.mod_toggle = Button(address=Address.DELAY__MOD)
        self.sync = Led(color=LedColor.RED, address=Address.DELAY__LED_SYNC)
        self.sync_toggle = Button(address=Address.DELAY__SYNC)
        self.learn = Button(address=Address.DELAY__LEARN)


class Feedback:
    _DISPLAY_SIZE = 2
    _SELECT_OPTIONS = 3

    display: Display
    select: LedMap
    level: Led
    high: Led
    low: Led
    feedback = Led
    feedback_up = Button
    feedback_down = Button
    inv = Led
    inv_toggle = Button
    select_toggle = Button

    def __init__(self):
        self.display = Display(self._DISPLAY_SIZE)
        self.display.digits[0].address = Address.FEEDBACK__DIGIT_1
        self.display.digits[1].address = Address.FEEDBACK__DIGIT_2
        self.select = LedMap(self._SELECT_OPTIONS)
        self.feedback = Led(color=LedColor.GREEN, address=Address.FEEDBACK__LED_F_BACK)
        self.feedback_up = Button(address=Address.FEEDBACK__UP)
        self.feedback_down = Button(address=Address.FEEDBACK__DOWN)
        self.inv = Led(color=LedColor.RED, address=Address.FEEDBACK__LED_INV)
        self.inv_toggle = Button(address=Address.FEEDBACK__INV)
        self.select_toggle = Button(address=Address.FEEDBACK__SELECT)

    @property
    def level(self):
        return self.select.leds[0]

    @property
    def high(self):
        return self.select.leds[1]

    @property
    def low(self):
        return self.select.leds[2]


class PresetSpec:
    _DISPLAY_SIZE = 2
    _MIX_SPEC_OPTIONS = 2

    display: Display
    mix_spec: LedMap
    sno: Led
    sva: Led
    preset: Led
    preset_up: Button
    preset_down: Button
    delay_on: Led
    delay: Button
    mix_spec_toggle: Button

    def __init__(self):
        self.display = Display(self._DISPLAY_SIZE)
        self.display.digits[0].address = Address.PRESET_SPEC__DIGIT_1
        self.display.digits[1].address = Address.PRESET_SPEC__DIGIT_2
        self.mix_spec = LedMap(self._MIX_SPEC_OPTIONS, address=Address.PRESET_SPEC__LEDS_MIX_SPEC)
        self.preset = Led(color=LedColor.GREEN, address=Address.PRESET_SPEC__LED_PRESET)
        self.preset_up = Button(address=Address.PRESET_SPEC__PRESET_UP)
        self.preset_down = Button(address=Address.PRESET_SPEC__PRESET_DOWN)
        self.delay_on = Led(color=LedColor.RED, address=Address.DELAY__LED_DELAY_ON)
        self.delay = Button(address=Address.PRESET_SPEC__DELAY)
        self.mix_spec_toggle = Button(address=Address.PRESET_SPEC__MIX_SPEC)

    @property
    def sno(self):
        return self.mix_spec.leds[0]

    @property
    def sva(self):
        return self.mix_spec.leds[1]


class Keyboard:
    seven: Button
    eight: Button
    nine: Button
    four: Button
    five: Button
    six: Button
    one: Button
    two: Button
    three: Button
    zero: Button
    dot: Button
    enter: Button

    def __init__(self):
        self.seven = Button(address=Address.KEYBOARD__7)
        self.eight = Button(address=Address.KEYBOARD__8)
        self.nine = Button(address=Address.KEYBOARD__9)
        self.four = Button(address=Address.KEYBOARD__4)
        self.five = Button(address=Address.KEYBOARD__5)
        self.six = Button(address=Address.KEYBOARD__6)
        self.one = Button(address=Address.KEYBOARD__1)
        self.two = Button(address=Address.KEYBOARD__2)
        self.three = Button(address=Address.KEYBOARD__3)
        self.zero = Button(address=Address.KEYBOARD__0)
        self.dot = Button(address=Address.KEYBOARD__DOT)
        self.enter = Button(address=Address.KEYBOARD__ENTER)


class Surface:
    brightness = Brightness()
    meters = Meters()
    modulation = Modulation()
    pan_dyn = PanDyn()
    delay = Delay()
    feedback = Feedback()
    preset_spec = PresetSpec()
    keyboard = Keyboard()

    def __init__(self):
        self._addresses_by_path = self._seek_address()
        self.address_map = self._map_addresses(self._addresses_by_path)

    def _seek_address(self, obj=None, root=None):
        addresses = {}
        if obj is None:
            obj = self
        if root is None:
            root = self.__class__.__name__
        for element in obj.__dir__():
            if element.startswith('_'):
                continue

            if element in (
                    'clear',
                    'copy',
                    'append',
                    'insert',
                    'extend',
                    'pop',
                    'remove',
                    'index',
                    'count',
                    'reverse',
                    'sort',
            ):
                continue

            try:
                addresses[root]
            except KeyError:
                addresses[root] = {}

            if hasattr(obj, 'address'):
                address = getattr(obj, 'address')
                if address:
                    addresses[root] = address
            else:
                next_obj = getattr(obj, element)
                if isinstance(next_obj, Iterable):
                    for i, sub_obj in enumerate(next_obj):
                        addresses[root][i] = {}
                        addresses[root][i].update(self._seek_address(sub_obj, i))
                else:
                    addresses[root].update(self._seek_address(next_obj, element))

        return addresses

    def _map_addresses(self, addr, prev_path=None):
        flipped = {}
        path = None
        for key, val in addr.items():
            if key == self.__class__.__name__:
                path = self
            if prev_path:
                if isinstance(key, int):
                    if hasattr(prev_path, 'digits'):
                        path = prev_path.digits[key]
                    elif hasattr(prev_path, 'leds'):
                        path = prev_path.leds[key]
                    else:
                        print(prev_path)
                else:
                    path = getattr(prev_path, key)
            if isinstance(val, Address):
                if not path:
                    raise RuntimeError("path not found. This should not happen")
                flipped[val] = path
                continue
            else:
                flipped.update(self._map_addresses(addr[key], path))
        return flipped
