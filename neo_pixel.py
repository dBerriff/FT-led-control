# neo_pixel.py
"""
    Control WS2812E/NeoPixel lighting
    This software takes a very basic approach to colour manipulation.
    For a far more sophisticated approach see
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
    
    ColourSpace provides RGB values for these strip and grid classes.
    Some object parameters are set post-instantiation because of MicroPython restrictions.
    List comprehension is avoided for performance reasons

    PixelStrip(NeoPixel)
    Set pixel output for a strip.

    PixelGrid(PixelStrip)
    Set pixel output for a rectangular grid.

"""

from machine import Pin
from neopixel import NeoPixel
from colour_space import ColourSpace as CS


class PixelStrip(NeoPixel):
    """ extend NeoPixel class with pixel-strip-related methods
    """

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.colours = CS.colours
        self.get_g_rgb = CS.get_rgb

    def set_pixel(self, index_, rgb_, level_):
        """ fill a  pixels with rgb colour """
        self[index_] = self.get_g_rgb(rgb_, level_)

    def set_strip(self, rgb_, level_):
        """ fill all pixels with rgb colour """
        g_rgb = self.get_g_rgb(rgb_, level_)
        for index in range(self.n):
            self[index] = g_rgb

    def set_range(self, index_, count_, rgb_, level_):
        """ fill count_ pixels with rgb_  """
        g_rgb = self.get_g_rgb(rgb_, level_)
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
            rgb_list.append(self.get_g_rgb(rgb_, level_))
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
        self.fill_grid = self.set_strip  # alias

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
        """ decrement cell col, row coordinate """
        c, r = coord
        c -= 1
        if c < 0:
            c = self.max_col
            r -= 1
            r %= self.n_rows
        return c, r

    def fill_col(self, col, rgb_, level_):
        """ fill col with rgb_ colour """
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = self.get_g_rgb(rgb_, level_)

    def fill_row(self, row, rgb_, level_):
        """ fill row with rgb_ colour """
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = self.get_g_rgb(rgb_, level_)

    def fill_diagonal(self, rgb_, level_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        if not mirror:
            for col in range(self.n_rows):
                self[self.coord_index[col, col]] = \
                    self.get_g_rgb(rgb_, level_)
        else:
            for col in range(self.n_rows):
                self[self.coord_index[self.max_col - col, col]] = \
                    self.get_g_rgb(rgb_, level_)

    def display_char(self, char_, rgb_, level_):
        """ display a single character in rgb_ """
        rgb = self.get_g_rgb(rgb_, level_)
        if char_ in self.charset:
            char_grid = self.charset[char_]
            for row in range(self.n_rows):
                for col in range(self.n_cols):
                    self[self.coord_index[col, row]] = \
                        rgb if char_grid[row][col] else (0, 0, 0)
        else:
            self.fill_grid((0, 0, 0))
