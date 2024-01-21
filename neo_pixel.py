# neo_pixel.py
""" drive NeoPixel strip lighting """

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

        Additional parameter:
        - gamma for visual intensity correction

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
        self.np_pin = np_pin
        self.n_pixels = n_pixels
        self.gamma = gamma  # 2.6: Adafruit suggested value
        self.rgb_gamma = self.get_rgb_gamma(self.gamma)  # conversion tuple
        self.name = str(np_pin)  # for debug/logging

    @staticmethod
    def get_rgb_gamma(gamma):
        """ return rgb gamma-compensation tuple """
        return tuple([round(pow(x / 255, gamma) * 255) for x in range(0, 256)])

    @staticmethod
    def get_rgb_level(rgb_, level_):
        """ return level-converted rgb value """
        return (rgb_[0] * level_ // 255,
                rgb_[1] * level_ // 255,
                rgb_[2] * level_ // 255)

    def get_rgb_g_corrected(self, rgb_, level_):
        """ return gamma-corrected rgb value
            - level in range(0, 256)
        """
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        rgb_l = self.get_rgb_level(rgb_, level_)
        rgb_c = (self.rgb_gamma[rgb_l[0]],
                 self.rgb_gamma[rgb_l[1]],
                 self.rgb_gamma[rgb_l[2]])
        return rgb_c

    def strip_fill_rgb(self, rgb, level):
        """ fill all pixels with rgb colour """
        rgb = self.get_rgb_g_corrected(rgb, level)
        for pixel in range(self.n_pixels):
            self.__setitem__(pixel, rgb)
