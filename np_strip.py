# np_strip.py
"""
    Control WS2812E/NeoPixel lighting
    This software takes a basic approach to colour manipulation.
    For far more sophisticated approaches see:
    - Adafruit Circuit Python
    - FastLED project.

    Adafruit documentation is acknowledged as a source of information,
    as is the FasLED documentation.
    See as an initial document:
    https://cdn-learn.adafruit.com/downloads/pdf/adafruit-neopixel-uberguide.pdf

    From micropython.org:
        class neopixel.NeoPixel(pin, n, *, bpp=3, timing=1)
        Construct a NeoPixel object. The parameters are:
        - pin is a machine.Pin instance
        - n is the number of LEDs in the strip
        - bpp is 3 for RGB LEDs, and 4 for RGBW LEDs
        - timing is 0 for 400kHz, and 1 for 800kHz LEDs (most are 800kHz)

    Classes:
    
    ColourSpace provides RGB values for PixelStrip and PixelGrid classes.
    Some object parameters are set post-instantiation because of MicroPython restrictions.
    List comprehension is generally avoided for (reported) performance reasons

    PixelStrip(NeoPixel)
    Set pixel output for a strip.

    PixelGrid(PixelStrip)
    Set pixel output for a rectangular grid.

    - implicit conversion of colour-keys to RGB has been removed
    - 'set_' functions do not write() pixels - allows for overlays
"""

from machine import Pin
from pio_ws2812 import Ws2812Strip


class PixelStrip(Ws2812Strip):
    """ extend NeoPixel class with pixel-strip-related methods
    """

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug

    def set_pixel_rgb(self, index_, rgb_):
        """ fill a pixel with rgb colour """
        self[index_] = rgb_

    def set_strip_rgb(self, rgb_):
        """ fill all pixels with rgb colour """
        for index in range(self.n):
            self[index] = rgb_

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with rgb_  """
        for _ in range(count_):
            index_ %= self.n
            self[index_] = rgb_
            index_ += 1

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with rgb_ """
        for index in index_list_:
            self[index] = rgb_

    def set_range_rgb_list_rgb(self, index_, count_, rgb_list):
        """ fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_ """
        n_rgb = len(rgb_list)
        c_index = 0
        for _ in range(count_):
            index_ %= self.n
            c_index %= n_rgb
            self[index_] = rgb_list[c_index]
            index_ += 1
            c_index += 1

    def clear(self):
        """ set and write all pixels to off """
        for index in range(self.n):
            self[index] = (0, 0, 0)
        self.write()
