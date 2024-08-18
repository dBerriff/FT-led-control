# pio_day-night.py
"""
    Classes:
    PimoroniRGB: set onboard tri-colour LED
    Plasma2040: written for Pimoroni Plasma 2040 board

    non-asyncio version
    
    - 2 + 1 buttons are hard-wired on the Pimoroni Plasma 2350:
        A, U (User, labelled BOOT) + RESET
"""

from machine import Pin, PWM, freq
from micropython import const
from buttons import Button, HoldButton


class PimoroniRGB:
    """ Pimoroni class to set Plasma 2350 hardwired RGB LED """

    r_gp = const(16)
    g_gp = const(17)
    b_gp = const(18)

    def __init__(self):
        self.led_r = PWM(Pin(self.r_gp), freq=1000)
        self.led_g = PWM(Pin(self.g_gp), freq=1000)
        self.led_b = PWM(Pin(self.b_gp), freq=1000)

    def set_rgb_u8(self, rgb):
        """ Pimoroni RGB LEDs require dc inversion """
        r = 255 - rgb[0]
        g = 255 - rgb[1]
        b = 255 - rgb[2]
        self.led_r.duty_u16(r * 257)
        self.led_g.duty_u16(g * 257)
        self.led_b.duty_u16(b * 257)


class Plasma:
    """
        Pimoroni Plasma series of boards
        - control WS2812/APA102 LED strip
        - hardwired GPIO pins are typically (see schematics):
            -- CLK, DATA: LED strip clock and data
            -- LED_R, LED_G, LED_B: onboard 3-colour LED
            -- SW_A, (SW_B), SW_U: user buttons
            -- I2C output (for LCD)
    """

    NAME = ''
    # Plasma 2040 GPIO pins

    # optional LCD1602 pins - available on QW/ST connector
    LCD_SDA = const(20)
    LCD_SCL = const(21)

    # pixel clock and data pins
    CLK = const(14)  # not used for WS2812
    DATA = const(15)

    # LCD1602 pins
    LCD_CLK = const(21)
    LCD_DATA = const(20)

    def __init__(self):
        self.led = PimoroniRGB()
        self.buttons = dict()

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb_u8(rgb_)


class Plasma2040(Plasma):
    """ Pimoroni Plasma 2040 """
    NAME = 'Plasma 2040'
    # Plasma 2040 GPIO pins
    SW_A = 12
    SW_B = 13
    SW_U = 23

    def __init__(self):
        super().__init__()
        self.buttons = {'A': Button(self.SW_A, pull_up=True, name='A'),
                        'B': HoldButton(self.SW_B, pull_up=True, name='B'),
                        'U': Button(self.SW_U, pull_up=False, name='U')
                        }


class Plasma2350(Plasma):
    """ Pimoroni Plasma 2350 """
    NAME = 'Plasma 2350'
    # Plasma 2350 GPIO pins
    SW_A = 12
    SW_U = 22

    def __init__(self):
        super().__init__()
        # pull_up must not be set for User button on this board
        self.buttons = {'A': Button(self.SW_A, name='A'),
                        'U': HoldButton(self.SW_U, name='U', pull_up=False)
                        }
