# led.py

""" LED-related classes """

from micropython import const
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
from neopixel import NeoPixel


class NPStrip(NeoPixel):
    """ extend NeoPixel class. From micropython.org:
        class neopixel.NeoPixel(pin, n, *, bpp=3, timing=1)
        Construct a NeoPixel object. The parameters are:
        - pin is a machine.Pin instance.
        - n is the number of LEDs in the strip.
        - bpp is 3 for RGB LEDs, and 4 for RGBW LEDs.
        - timing is 0 for 400kHz, and 1 for 800kHz LEDs (most are 800kHz).

    """
    # basic gamma correction tuple
    GAMMA = (
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
        2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
        5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10,
        10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
        17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
        25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
        37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
        51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
        69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
        90, 92, 93, 95, 96, 98, 99, 101,102, 104, 105, 107, 109, 110, 112, 114,
        115, 117, 119, 120, 122, 124, 126, 127, 129, 131, 133, 135, 137, 138, 140, 142,
        144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 167, 169, 171, 173, 175,
        177, 180, 182, 184, 186, 189, 191, 193, 196, 198, 200, 203, 205, 208, 210, 213,
        215, 218, 220, 223, 225, 228, 231, 233, 236, 239, 241, 244, 247, 249, 252, 255
        )

    # selected colours as on/off rgb values
    Colours = {
        'WHT': (1, 1, 1),
        'BLK': (0, 0, 0),
        'RED': (1, 0, 0),
        'GRN': (0, 1, 0),
        'BLU': (0, 0, 1),
        'CYN': (0, 1, 1),
        'MGT': (1, 0, 1),
        'YEL': (1, 1, 0)}

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin
        self.n_pixels = n_pixels
        self.name = str(np_pin)
        self.n_pixels = n_pixels

    def colour_rgb(self, colour, level):
        """ set pixel 0 to n-1 to RGB colour """
        if colour in self.Colours:
            r, g, b = self.Colours[colour]
            return r * level, g * level, b * level
        else:
            return 0, 0, 0

    def set_pixel_rgb(self, pixel, rgb):
        """ set pixel 0 to n-1 to RGB colour """
        self[pixel] = (
            self.GAMMA[rgb[0]], self.GAMMA[rgb[1]], self.GAMMA[rgb[2]])

    def strip_fill_rgb(self, pixel, count, rgb):
        """ fill a range of pixels with rgb colour """
        pass

    """ from Raspberry Pi Pico Python SDK 3.9.2. WS2812 LED (NeoPixel) """
    @asm_pio(sideset_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
    def ws2812():
        T1 = 2
        T2 = 5
        T3 = 3
        wrap_target()
        label("bitloop")
        out(x, 1)               .side(0)    [T3 - 1]
        jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
        jmp("bitloop")          .side(1)    [T2 - 1]
        label("do_zero")
        nop()                   .side(0)    [T2 - 1]
        wrap()
