# pio_day-night.py
"""
    Classes:
    PimoroniRGB: set onboard tri-colour LED
    Plasma: abstract class for Pimoroni Plasma boards
    Plasma2040: Plasma 2040 board
    Plasma2350: Plasma 2350 board
"""

from machine import Pin, PWM, freq
from micropython import const
from buttons import HoldButton


class PimoroniRGB:
    """ Plasma hardwired RGB LED """

    R_GP = const(16)
    G_GP = const(17)
    B_GP = const(18)

    def __init__(self):
        self.led_r = PWM(Pin(self.R_GP), freq=1000)
        self.led_g = PWM(Pin(self.G_GP), freq=1000)
        self.led_b = PWM(Pin(self.B_GP), freq=1000)

    def set_rgb_u8(self, rgb):
        """ RGB LEDs require dc inversion """
        self.led_r.duty_u16((255 - rgb[0]) * 257)
        self.led_g.duty_u16((255 - rgb[1]) * 257)
        self.led_b.duty_u16((255 - rgb[2]) * 257)


class Plasma:
    """
        Pimoroni Plasma series of boards
        - control WS2812/APA102 LED strip
        - hardwired GPIO pins are typically (see schematics):
            -- strip_pins: LED strip
            -- i2c_pins: for LCD
    """

    NAME = ''
    strip_pins = {'clk': 14, 'dat': 15}
    i2c_pins = {'sda': 20, 'scl': 21}

    def __init__(self):
        self.led = PimoroniRGB()
        self.buttons = dict()

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb_u8(rgb_)


class Plasma2040(Plasma):
    """ Pimoroni Plasma 2040 """
    NAME = 'Plasma 2040'
    BOARD_BTNS = {'A': 12, 'B': 13, 'U': 23}

    def __init__(self):
        super().__init__()
        # click/hold buttons
        self.buttons = {'A': HoldButton(self.BOARD_BTNS['A'], name='A'),
                        'B': HoldButton(self.BOARD_BTNS['B'], name='B'),
                        'U': HoldButton(self.BOARD_BTNS['U'], name='U')
                        }


class Plasma2350(Plasma):
    """ Pimoroni Plasma 2350 """
    NAME = 'Plasma 2350'
    BOARD_BTNS = {'A': 12, 'U': 22}

    def __init__(self):
        super().__init__()
        # click/hold buttons
        self.buttons = {'A': HoldButton(self.BOARD_BTNS['A'], name='A'),
                        'U': HoldButton(self.BOARD_BTNS['U'], name='U')
                        }
