# dh_2040.py
"""
    Stub
    ! For a specific Pico-based installation. Constant values reminder !
    Dh2040: written for Pi Pico 1 board
    -  asyncio version
"""

from micropython import const
from buttons import Button, HoldButton


class Dh2040:
    """
        Pi Pico RP2040
        - control WS2812 LED strip
        - GPIO pins (see schematic and constants below):
            -- SW_A, SW_B, SW_U: user buttons, Pimoroni labels
            -- CLK, DATA: LED strip (WS2812) data not used
            -- LCD_SCL, LCD_SDA: for I2C display
    """
    # switch pins
    SW_A = const(10)
    SW_B = const(11)
    SW_U = const(13)

    # WS2812 pins
    CLK = const(0)
    DATA = const(0)

    # LCD pins/frequency
    LCD_SDA = const(2)
    LCD_SCL = const(3)
    FREQ = 10_000

    def __init__(self):
        self.buttons = {'A': Button(self.SW_A, pull_up=True, 'A'),
                        'B': HoldButton(self.SW_B, pull_up=True, 'B'),
                        'U': Button(self.SW_U, pull_up=True, 'U')
                        }
