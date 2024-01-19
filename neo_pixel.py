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
        
        Adafruit documentation is acknowledged as the main reference for this work.
        See as an initial reference:
        https://cdn-learn.adafruit.com/downloads/pdf/adafruit-neopixel-uberguide.pdf

    """

    # selected colours as rgb "full-on" values
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

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin
        self.n_pixels = n_pixels
        self.name = str(np_pin)
        self.gamma = 2.6  # Adafruit value
        self.rgb_gamma = self.get_rgb_gamma()

    def get_rgb_gamma(self):
        """ return rgb gamma conversion tuple """
        return tuple([round(pow(x / 255, self.gamma) * 255) for x in range(0, 256)])

    def set_pixel_rgb(self, pixel, rgb, level):
        """ set NPStrip[pixel] to rgb colour
            - level is with ref to 255
            - consider using float maths
        """
        r = rgb[0] * level // 255
        g = rgb[1] * level // 255
        b = rgb[2] * level // 255
        self[pixel] = (
            self.rgb_gamma[r], self.rgb_gamma[g], self.rgb_gamma[b])

    def strip_fill_rgb(self, rgb, level):
        """ fill all pixels with rgb colour """
        for i in range(self.n_pixels):
            self.set_pixel_rgb(i, rgb, level)

    def get_gamma_rgb(self, rgb, level):
        """ for testing and debug """
        level = max(level, 0)
        level = min(level, 255)
        r = rgb[0] * level // 255
        g = rgb[1] * level // 255
        b = rgb[2] * level // 255
        return self.rgb_gamma[r], self.rgb_gamma[g], self.rgb_gamma[b]

    def hsv(self, hue, saturation, value):
        """ return (R, G, B) values for HSV colour """
        return 0, 0, 0
