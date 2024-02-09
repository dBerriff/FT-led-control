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
    List comprehension is avoided for performance reasons

    PixelStrip(NeoPixel)
    Set pixel output for a strip.

    PixelGrid(PixelStrip)
    Set pixel output for a rectangular grid.

    Colours can be set by name (example: 'red') or RGB tuple (example: (255, 0, 0))
    Level should be set from a minimum of 0 to a maximum of 255
    Basic gamma correction is applied to all 3 RGB values by list lookup.
"""

from machine import Pin
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
        """ fill a  pixels with rgb colour """
        self[index_] = self.get_rgb(rgb_, level_)

    def set_strip(self, rgb_, level_):
        """ fill all pixels with rgb colour """
        g_rgb = self.get_rgb(rgb_, level_)
        for index in range(self.n):
            self[index] = g_rgb

    def set_range(self, index_, count_, rgb_, level_):
        """ fill count_ pixels with rgb_  """
        g_rgb = self.get_rgb(rgb_, level_)
        for _ in range(count_):
            index_ %= self.n
            self[index_] = g_rgb
            index_ += 1

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

    def clear(self):
        """ write all pixels to off """
        for index in range(self.n):
            self[index] = (0, 0, 0)
        self.write()


class PixelGrid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting grid
        - grid is wired 'snake' style; coord_index dict corrects
    """

    def __init__(self, np_pin, n_cols_, n_rows_):
        self.n_pixels = n_cols_ * n_rows_
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels)
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        self.coord_index = self.get_coord_index_dict()
        self.charset = None  # char_set assigned externally
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

    def fill_col(self, col, rgb_, level_):
        """ fill col with rgb_ colour """
        rgb = self.get_rgb(rgb_, level_)
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb

    def fill_row(self, row, rgb_, level_):
        """ fill row with rgb_ colour """
        rgb = self.get_rgb(rgb_, level_)
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb

    def fill_diagonal(self, rgb_, level_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        rgb = self.get_rgb(rgb_, level_)
        if not mirror:
            for col in range(self.n_rows):
                self[self.coord_index[col, col]] = rgb
        else:
            for col in range(self.n_rows):
                self[self.coord_index[self.max_col - col, col]] = rgb

    def set_pixel_list(self, coord_list_, rgb_, level_):
        """ set a list of pixels
            - helps with char overlay
            - spaces are skipped; coord_list_ is None
        """
        if coord_list_:
            rgb = self.get_rgb(rgb_, level_)
            for c in coord_list_:
                self[self.coord_index[c]] = rgb

    def get_char_coords(self, char_):
        """ return char coords
            - does not belong in this class?
        """
        if char_ in self.charset:
            if char_ == ' ':
                return None
            char_grid = self.charset[char_]
            coord_list = []
            # chars are stored as a list of rows
            for row in range(self.n_rows):
                for col in range(self.n_cols):
                    if char_grid[row][col] == 1:
                        coord_list.append((col, row))
            return tuple(coord_list)
