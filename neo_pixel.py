# neo_pixel.py
""" drive NeoPixel strip lighting """

import asyncio
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

        Additional methods extending class:
        - get_rgb_gamma(gamma):
            - return a tuple of gamma-corrected rgb levels for range(0, 256)
            - used for speed of conversion
        - get_rgb_level(rgb, level):
            - colours are defined reference 255 peak intensity;
                return rgb tuple adjusted to lower level
        - get_rgb_g_corrected(rgb_):
            - return gamma-corrected rgb tuple
        - strip_fill_rgb(rgb, level):
            - set all NeoPixels in a strip to a common rgb value
        - dim(pixel, colour, level, period_ms=500):
            - dim a NeoPixel from an initial rgb value to off over period_ms

        Adafruit documentation is acknowledged as the main reference for this work.
        See as an initial reference:
        https://cdn-learn.adafruit.com/downloads/pdf/adafruit-neopixel-uberguide.pdf

    """

    # selection of colours as rgb values (full intensity)
    # see: https://docs.circuitpython.org/projects/led-animation/en/latest/
    #      api.html#adafruit-led-animation-color
    Colours = {
        'amber': (255, 100, 0),
        'aqua': (50, 255, 255),
        'black': (0, 0, 0),
        'blue': (0, 0, 255),
        'cyan': (0, 255, 255),
        'gold': (255, 255, 30),
        'green': (0, 255, 0),
        'jade': (0, 255, 40),
        'magenta': (255, 0, 255),
        'old_lace': (253, 245, 230),
        'orange': (255, 40, 0),
        'pink': (242, 90, 255),
        'purple': (180, 0, 255),
        'red': (255, 0, 0),
        'teal': (0, 255, 120),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0)
        }

    def __init__(self, np_pin, n_pixels, gamma=2.6):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.n_pixels = n_pixels
        self.gamma = gamma  # 2.6: Adafruit suggested value
        self.rgb_gamma = self.get_rgb_gamma(self.gamma)

    @staticmethod
    def get_rgb_gamma(gamma):
        """ return rgb gamma-compensation tuple """
        return tuple([round(pow(x / 255, gamma) * 255) for x in range(0, 256)])

    @staticmethod
    def get_rgb_level(rgb_, level_):
        """ return level-converted rgb value """
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return (rgb_[0] * level_ // 255,
                rgb_[1] * level_ // 255,
                rgb_[2] * level_ // 255)

    def get_rgb_g_corrected(self, rgb_):
        """ return gamma-corrected rgb value
            - level in range(0, 256)
        """
        return (self.rgb_gamma[rgb_[0]],
                self.rgb_gamma[rgb_[1]],
                self.rgb_gamma[rgb_[2]])

    def strip_fill_rgb(self, rgb_):
        """ fill all pixels with rgb colour
            - blocks asyncio scheduler """
        for pixel in range(self.n_pixels):
            self.__setitem__(pixel, rgb_)

    async def as_strip_fill_rgb(self, rgb_):
        """ fill all pixels with rgb colour as coro()
            - scheduler adds significant overhead """
        for pixel in range(self.n_pixels):
            self.__setitem__(pixel, rgb_)
            await asyncio.sleep_ms(0)

    async def dim_gamma(self, pixel, colour_, level_, period_ms=500):
        """ dim pixel to zero applying gamma correction """
        pause = period_ms // level_
        while level_ > 0:
            rgb = self.get_rgb_g_corrected(self.get_rgb_level(colour_, level_))
            self.__setitem__(pixel, rgb)
            self.write()
            await asyncio.sleep_ms(pause)
            if rgb == (0, 0, 0):
                break
            level_ -= 1
