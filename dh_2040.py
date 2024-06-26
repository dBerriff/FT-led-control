# dh_2040.py
"""
    ! For a specific Pico-based installation. Constant values.
    Classes:
    Dh2040: written for standard Pi Pico board
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
    SW_A = const(11)
    SW_B = const(12)
    SW_U = const(10)

    # WS2812 pins
    CLK = const(0)
    DATA = const(0)

    # LCD pins/frequency
    LCD_SDA = const(2)
    LCD_SCL = const(3)
    FREQ = 10_000

    def __init__(self):
        self.buttons = {'A': Button(self.SW_A, 'A'),
                        'B': HoldButton(self.SW_B, 'B'),
                        'U': Button(self.SW_U, 'U')
                        }
