# neo_pixel.py
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
from neopixel import NeoPixel
import json
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


class PixelGrid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting grid
        - grid is wired 'snake' style;
            coord_index dict corrects by lookup
    """
    
    BLOCK_SIZE = 8

    def __init__(self, np_pin, n_cols_, n_rows_, cs_file):
        self.n_pixels = n_cols_ * n_rows_
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels)
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.block_cols = self.BLOCK_SIZE
        self.block_rows = self.BLOCK_SIZE
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        self.max_block_col = self.block_cols - 1
        self.max_block_row = self.block_rows - 1
        self.coord_index = self.get_coord_index_dict()
        self.charset = self.get_char_indices(cs_file)
        self.set_grid = self.set_strip  # alias

    def get_coord_index_dict(self):
        """ correct the grid 'snake' addressing scheme
            (c, r) coord -> list index
            - cols left to right, rows top to bottom
        """
        c_i_dict = {}
        max_row = self.max_row  # avoid repeated dict access
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                if col % 2 == 1:  # odd row
                    i = max_row - row
                else:
                    i = row
                c_i_dict[col, row] = col * self.n_rows + i
        return c_i_dict

    def coord_inc(self, coord):
        """ increment (col, row) coordinate """
        c, r = coord
        c += 1
        if c > self.max_col:
            c = 0
            r += 1
            r %= self.n_rows
        return c, r

    def coord_dec(self, coord):
        """ decrement (col, row) coordinate """
        c, r = coord
        c -= 1
        if c < 0:
            c = self.max_col
            r -= 1
            r %= self.n_rows
        return c, r

    def set_col(self, col, rgb_, level_):
        """ fill col with rgb_ colour """
        rgb_ = self.get_rgb(rgb_, level_)
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb_

    def set_row(self, row, rgb_, level_):
        """ fill row with rgb_ colour """
        rgb_ = self.get_rgb(rgb_, level_)
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb_

    def set_diagonal(self, rgb_, level_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        rgb = self.get_rgb(rgb_, level_)
        if not mirror:
            for col in range(self.block_cols):
                self[self.coord_index[col, col]] = rgb
        else:
            for col in range(self.block_cols):
                self[self.coord_index[self.max_block_col - col, col]] = rgb

    def set_coord_list(self, coord_list_, rgb_, level_):
        """ set a list of pixels by coords """
        if coord_list_:
            rgb = self.get_rgb(rgb_, level_)
            for c in coord_list_:
                self[self.coord_index[c]] = rgb

    @staticmethod
    def get_char_indices(file_name):
        """ return char pixel indices """
        with open(file_name, 'r') as f:
            retrieved = json.load(f)
        for ch in retrieved:
            retrieved[ch] = tuple(retrieved[ch])
        return retrieved
