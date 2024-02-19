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

    - Colours can be set by name (example: 'red') or RGB tuple (example: (255, 0, 0)), except:
        -- method names ending _rgb require an RGB tuple to reduce computation time
    - Level should be set from a minimum of 0 to a maximum of 255
    - Basic gamma correction is applied to all 3 RGB values by list lookup
    - 'set_' functions do not write() pixels - allows for overlays
"""

from machine import Pin
import asyncio
from random import randrange
from neopixel import NeoPixel
from colour_space import ColourSpace


class PixelStrip(NeoPixel):
    """ extend NeoPixel class with pixel-strip-related methods
    """

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.cs = ColourSpace()

    def set_pixel(self, index_, clr_, level_):
        """ fill a pixel with rgb colour """
        self[index_] = self.get_rgb(clr_, level_)

    def set_pixel_rgb(self, index_, rgb_):
        """ fill a pixel with rgb colour """
        self[index_] = rgb_

    def set_strip(self, clr_, level_):
        """ fill all pixels with rgb colour """
        rgb = self.cs.get_rgb(clr_, level_)
        for index in range(self.n):
            self[index] = rgb

    def set_strip_rgb(self, rgb_):
        """ fill all pixels with rgb colour """
        for index in range(self.n):
            self[index] = rgb_

    def set_range(self, index_, count_, clr_, level_):
        """ fill count_ pixels with rgb_  """
        rgb = self.cs.get_rgb(clr_, level_)
        for _ in range(count_):
            index_ %= self.n
            self[index_] = rgb
            index_ += 1

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with rgb_  """
        for _ in range(count_):
            index_ %= self.n
            self[index_] = rgb_
            index_ += 1

    def set_list(self, index_list_, clr_, level_):
        """ fill index_list pixels with rgb_ at set level_ """
        rgb = self.cs.get_rgb(clr_, level_)
        for index in index_list_:
            self[index] = rgb

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with rgb_ """
        for index in index_list_:
            self[index] = rgb_

    def set_range_c_list(self, index_, count_, colour_list, level_):
        """ fill count_ pixels with list of colour values
            - n_clrs does not have to equal count_ """
        n_clrs = len(colour_list)
        rgb_list = []
        for rgb_ in colour_list:
            rgb_list.append(self.cs.get_rgb(rgb_, level_))
        c_index = 0
        for _ in range(count_):
            index_ %= self.n
            c_index %= n_clrs
            self[index_] = rgb_list[c_index]
            index_ += 1
            c_index += 1

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

    # helper methods

    async def np_arc_weld(self, pixel_):
        """ coro: single pixel:
            simulate arc-weld flash and decay
        """
        arc_rgb_ = 'white'
        glow_rgb_ = 'red'
        for _ in range(2):
            for _ in range(randrange(100, 200)):
                level = randrange(127, 256)
                self[pixel_] = self.get_rgb(arc_rgb_, level)
                self.write()
                await asyncio.sleep_ms(20)
            for level in range(160, -1, -1):
                self[pixel_] = self.get_rgb(glow_rgb_, level)
                self.write()
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(randrange(1_000, 5_000))

    async def np_twinkler(self, pixel_):
        """ coro: single pixel:
            simulate gas-lamp twinkle
        """
        lamp_rgb = (0xff, 0xcf, 0x9f)
        base_level = 64
        dim_level = 95
        n_smooth = 3
        # levels list: take mean value
        levels = [0] * n_smooth
        l_index = 0
        for _ in range(100):
            twinkle = randrange(64, 128, 8)
            # randrange > 0; no 'pop'
            if randrange(0, 50) > 0:  # most likely
                levels[l_index] = base_level + twinkle
                level = sum(levels) // n_smooth
            # randrange == 0; 'pop'
            else:
                # set 'pop' across levels list
                for i in range(n_smooth):
                    levels[i] = dim_level
                level = dim_level
            self[pixel_] = self.get_rgb(lamp_rgb, level)
            self.write()
            await asyncio.sleep_ms(randrange(20, 200, 20))
            l_index += 1
            l_index %= n_smooth

    async def mono_chase(self, rgb_list, pause=20):
        """ np strip:
            fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_
        """
        n_pixels = self.n
        n_colours = len(rgb_list)
        index = 0
        for _ in range(100):
            for i in range(n_colours):
                self[(index + i) % n_pixels] = rgb_list[i]
            self.write()
            await asyncio.sleep_ms(pause)
            self[index] = (0, 0, 0)
            index = (index + 1) % n_pixels

    async def colour_chase(self, rgb_list, pause=20):
        """ np strip:
            fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_
        """
        n_pixels = self.n
        n_rgb = len(rgb_list)
        c_index = 0
        for _ in range(100):
            for i in range(n_pixels):
                self[i] = rgb_list[(i + c_index) % n_rgb]
            self.write()
            await asyncio.sleep_ms(pause)
            c_index = (c_index - 1) % n_rgb
