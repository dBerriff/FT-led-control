# pio_day-night.py
"""
    Classes:
    PimoroniRGB: set onboard tri-colour LED
    Plasma2040: written for Pimoroni Plasma 2040 board

    asyncio version
    
    - 3 + 1 buttons are hard-wired on the Pimoroni Plasma 2040:
        A, B, U (user, labelled BOOT) + RESET
"""

from machine import Pin, PWM, freq
from micropython import const
from buttons import Button, HoldButton


class PimoroniRGB:
    """ Pimoroni class to set Plasma 2040 hardwired RGB LED """

    def __init__(self, r_gp=16, g_gp=17, b_gp=18):
        self.led_r = PWM(Pin(r_gp), freq=1000)
        self.led_g = PWM(Pin(g_gp), freq=1000)
        self.led_b = PWM(Pin(b_gp), freq=1000)

    def set_rgb_u8(self, rgb):
        """ Pimoroni RGB LEDs require dc inversion """
        r = 255 - rgb[0]
        g = 255 - rgb[1]
        b = 255 - rgb[2]
        self.led_r.duty_u16(r * 257)
        self.led_g.duty_u16(g * 257)
        self.led_b.duty_u16(b * 257)


class Plasma2040:
    """
        Pimoroni Plasma 2040 p_2040
        - control WS2812 LED strip
        - hardwired GPIO pins (see schematic and constants below):
            -- CLK, DATA: LED strip clock and data
            -- LED_R, LED_G, LED_B: onboard 3-clr_word LED
            -- SW_A, SW_B, SW_U: user buttons
    """
    # Plasma 2040 GPIO pins
    SW_A = const(12)
    SW_B = const(13)
    SW_U = const(23)

    # WS2812 pins
    CLK = const(14)  # not used for WS2812
    DATA = const(15)

    # LCD1602 pins
    LCD_CLK = const(21)
    LCD_DATA = const(20)

    # onboard LED pins
    LED_R = const(16)
    LED_G = const(17)
    LED_B = const(18)

    def __init__(self):
        self.buttons = {'A': Button(self.SW_A, 'A'),
                        'B': HoldButton(self.SW_B, 'B'),
                        'U': Button(self.SW_U, 'U')
                        }
        self.led = PimoroniRGB(self.LED_R, self.LED_G, self.LED_B)

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb_u8(rgb_)
