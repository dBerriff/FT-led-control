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

    - Colours can be set by name (example: 'red') or RGB tuple (example: (255, 0, 0))
    - Level should be set from a minimum of 0 to a maximum of 255
    - Basic gamma correction is applied to all 3 RGB values by list lookup
    - 'set_' functions do not write() pixels - allows for overlays
"""

from machine import Pin
import asyncio
from random import randrange
from neopixel import NeoPixel
from colour_space import ColourSpace as Cs


class PixelStrip(NeoPixel):
    """ extend NeoPixel class with pixel-strip-related methods
    """

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.colours = Cs.colours
        self.get_rgb = Cs.get_rgb

    def set_pixel(self, index_, rgb_, level_):
        """ fill a pixel with rgb colour """
        rgb_ = self.get_rgb(rgb_, level_)
        self[index_] = rgb_

    def set_pixel_rgb(self, index_, rgb_):
        """ fill a pixel with rgb colour """
        self[index_] = rgb_

    def set_strip(self, rgb_, level_):
        """ fill all pixels with rgb colour """
        rgb_ = self.get_rgb(rgb_, level_)
        for index in range(self.n):
            self[index] = rgb_

    def set_strip_rgb(self, rgb_):
        """ fill all pixels with rgb colour """
        for index in range(self.n):
            self[index] = rgb_

    def set_range(self, index_, count_, rgb_, level_):
        """ fill count_ pixels with rgb_  """
        rgb_ = self.get_rgb(rgb_, level_)
        for _ in range(count_):
            index_ %= self.n
            self[index_] = rgb_
            index_ += 1

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with rgb_  """
        for _ in range(count_):
            index_ %= self.n
            self[index_] = rgb_
            index_ += 1

    def set_list(self, index_list_, rgb_, level_):
        """ fill index_list pixels with rgb_ at set level_ """
        rgb_ = self.get_rgb(rgb_, level_)
        for index in index_list_:
            self[index] = rgb_

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with rgb_ """
        for index in index_list_:
            self[index] = rgb_

    def set_range_c_list(self, index_, count_, colour_list, level_):
        """ fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_ """
        n_colours = len(colour_list)
        rgb_list = []
        for rgb_ in colour_list:
            rgb_list.append(self.get_rgb(rgb_, level_))
        c_index = 0
        for _ in range(count_):
            index_ %= self.n
            c_index %= n_colours
            self[index_] = rgb_list[c_index]
            index_ += 1
            c_index += 1

    def set_range_c_list_rgb(self, index_, count_, colour_list):
        """ fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_ """
        n_colours = len(colour_list)
        c_index = 0
        for _ in range(count_):
            index_ %= self.n
            c_index %= n_colours
            self[index_] = colour_list[c_index]
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
        n_colours = len(rgb_list)
        c_index = 0
        for _ in range(100):
            for i in range(n_pixels):
                self[i] = rgb_list[(i + c_index) % n_colours]
            self.write()
            await asyncio.sleep_ms(pause)
            c_index = (c_index - 1) % n_colours


class ColourSignal:
    """
        model railway colour signals
        - level_ is required
    """

    # change keys to match layout terminology

    def __init__(self, nps_, pixel_, level_):
        self.nps = nps_
        self.pixel = pixel_
        self.c_red = nps_.get_rgb('red', level_)
        self.c_yellow = nps_.get_rgb('yellow', level_)
        self.c_green = nps_.get_rgb('green', level_)
        self.c_off = (0, 0, 0)


class FourAspect(ColourSignal):
    """ model UK 4-aspect colour signal
        - bottom to top: red-yellow-green-yellow
    """
    aspect_codes = {
        'stop': 0,
        'danger': 0,
        'red': 0,
        'caution': 1,
        'yellow': 1,
        'single yellow': 1,
        'preliminary caution': 2,
        'double yellow': 2,
        'clear': 3,
        'green': 3
    }

    # (r, y, g, y)
    settings = {
        0: (1, 0, 0, 0),
        1: (0, 1, 0, 0),
        2: (0, 1, 0, 1),
        3: (0, 0, 1, 0)
    }

    def __init__(self, nps_, pixel_, level_):
        super().__init__(nps_, pixel_, level_)
        self.i_red = pixel_
        self.i_yw1 = pixel_ + 1
        self.i_grn = pixel_ + 2
        self.i_yw2 = pixel_ + 3
        self.set_aspect('red')

    def set_aspect(self, aspect):
        """
            set signal aspect by number or code:
            0 - red
            1 - single yellow
            2 - double yellow
            3 - green
        """
        if isinstance(aspect, str):
            if aspect in self.aspect_codes:
                aspect = self.aspect_codes[aspect]
            else:
                aspect = self.aspect_codes['red']
        setting = self.settings[aspect]
        self.nps[self.i_red] = self.c_red if setting[0] == 1 else self.c_off
        self.nps[self.i_yw1] = self.c_yellow if setting[1] == 1 or setting[3] else self.c_off
        self.nps[self.i_grn] = self.c_green if setting[2] == 1 else self.c_off
        self.nps[self.i_yw2] = self.c_yellow if setting[3] == 1 else self.c_off
        self.nps.write()

    def set_by_blocks_clear(self, clr_blocks):
        """ set aspect by clear blocks """
        clr_blocks = min(clr_blocks, 3)  # > 3 clear is still 'green'
        self.set_aspect(clr_blocks)
