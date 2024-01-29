# neo_pixel.py
""" drive WS2812E/NeoPixel strip lighting """

import asyncio
from micropython import const
from machine import Pin
from collections import namedtuple
from neopixel import NeoPixel


class PixelStrip(NeoPixel):
    """ extend NeoPixel class. From micropython.org:
        class neopixel.NeoPixel(pin, n, *, bpp=3, timing=1)
        Construct a NeoPixel object. The parameters are:
        - pin is a machine.Pin instance.
        - n is the number of LEDs in the strip.
        - bpp is 3 for RGB LEDs, and 4 for RGBW LEDs.
        - timing is 0 for 400kHz, and 1 for 800kHz LEDs (most are 800kHz).

        Additional methods extending class:
        - get_rgb_gamma_tuple(gamma):
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

    OFF = const((0, 0, 0))

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
        'orange': (255, 140, 0),  # dark orange g=140; g=165 for full
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
        self.rgb_gamma = tuple(
            [round(pow(x / 255, gamma) * 255) for x in range(0, 256)])

    @staticmethod
    def get_rgb_l(rgb_, level_):
        """ return level-converted rgb value """
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return (rgb_[0] * level_ // 255,
                rgb_[1] * level_ // 255,
                rgb_[2] * level_ // 255)

    def get_rgb_g_c(self, rgb_):
        """ return gamma-corrected rgb value """
        return (self.rgb_gamma[rgb_[0]],
                self.rgb_gamma[rgb_[1]],
                self.rgb_gamma[rgb_[2]])

    def get_rgb_l_g_c(self, rgb_, level_):
        """ return level-converted, gamma-corrected rgb value
            - level in range(0, 256)
        """
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return (self.rgb_gamma[rgb_[0] * level_ // 255],
                self.rgb_gamma[rgb_[1] * level_ // 255],
                self.rgb_gamma[rgb_[2] * level_ // 255])

    def fill_strip(self, rgb_):
        """ fill all pixels with rgb colour
            - blocking
        """
        for pixel in range(self.n_pixels):
            self[pixel] = rgb_

    async def as_fill_strip(self, rgb_):
        """ fill all pixels with rgb colour as coro()
            - non-blocking but scheduler adds overhead
        """
        for pixel in range(self.n_pixels):
            self[pixel] = rgb_
            await asyncio.sleep_ms(0)

    async def dim_g_c(self, pixel, colour_, level_, period_ms=500):
        """ dim pixel, applying gamma correction """
        pause = period_ms // level_
        while level_ > 0:
            rgb = self.get_rgb_l_g_c(colour_, level_)
            self[pixel] = rgb
            self.write()
            await asyncio.sleep_ms(pause)
            if rgb == (0, 0, 0):
                break
            level_ -= 1


class PixelGrid(PixelStrip):
    """ extend NPixelStrip to support BTF-Lighting grid
        - grid is wired 'snake' style; coord_index dict corrects
    """

    Coord = namedtuple('Coord', ['c', 'r'])

    def __init__(self, np_pin, n_cols, n_rows, gamma=2.6):
        self.n_pixels = n_cols * n_rows
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels, gamma)
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.max_col = n_cols - 1
        self.max_row = n_rows - 1
        self.c_r_dim = self.Coord(self.n_cols, self.n_rows)
        self.coord_index = self.get_coord_index_dict()
        self.charset = None
        self.fill_grid = self.fill_strip  # method alias

    def get_coord_index_dict(self):
        """ correct grid addressing scheme
            - columns left to right, rows top to bottom
        """
        coord_index_dict = {}
        max_row = self.max_row  # avoid repeated dict access
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                if col % 2:  # odd row
                    r = max_row - row
                else:
                    r = row
                coord_index_dict[col, row] = col * self.n_rows + r
        return coord_index_dict

    def coord_inc(self, coord):
        """ increment cell coordinate """
        c = coord.c + 1
        r = coord.r
        if c == self.n_cols:
            c = 0
            r += 1
            r %= self.n_rows
        return self.Coord(c, r)

    def coord_dec(self, coord):
        """ decrement cell coordinate """
        c = coord.c - 1
        r = coord.r
        if c == -1:
            c = self.max_col
            r -= 1
            r %= self.n_rows
        return self.Coord(c, r)

    def fill_row(self, row, rgb):
        """ fill row with rgb value"""
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb

    def fill_col(self, col, rgb):
        """ fill col with rgb value"""
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb

    def fill_diagonal(self, rgb, reverse=False):
        """ fill diagonal with rgb value
            - assumes square grid!
        """
        if reverse:
            for col in range(self.n_cols):
                r_col = self.max_col - col
                self[self.coord_index[r_col, col]] = rgb
        else:
            for col in range(self.n_cols):
                self[self.coord_index[col, col]] = rgb

    def display_char(self, char_, rgb_):
        """ display char_ in colour rgb_ """
        if char_ in self.charset:
            char_grid = self.charset[char_]
            for row in range(self.n_rows):
                for col in range(self.n_cols):
                    if char_grid[row][col]:
                        self[self.coord_index[col, row]] = rgb_
                    else:
                        self[self.coord_index[col, row]] = self.OFF
        else:
            self.fill_grid(self.OFF)
        self.write()

    async def display_string(self, str_, rgb_, pause=500):
        """ cycle through the letters in a string """
        for char_ in str_:
            self.display_char(char_, rgb_)
            await asyncio.sleep_ms(pause)
