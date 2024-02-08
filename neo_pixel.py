# neo_pixel.py
"""
    Control WS2812E/NeoPixel lighting
    From micropython.org:
        class neopixel.NeoPixel(pin, n, *, bpp=3, timing=1)
        Construct a NeoPixel object. The parameters are:
        - pin is a machine.Pin instance
        - n is the number of LEDs in the strip
        - bpp is 3 for RGB LEDs, and 4 for RGBW LEDs
        - timing is 0 for 400kHz, and 1 for 800kHz LEDs (most are 800kHz)

    Adafruit documentation is acknowledged as the main reference for this work.
    See as an initial document:
    https://cdn-learn.adafruit.com/downloads/pdf/adafruit-neopixel-uberguide.pdf

    Classes:

    PixelStrip(NeoPixel)
    The MicroPython class NeoPixel is inherited and
    extended so that colours can be set with gamma correction.
    LED intensity is represented on an 8-bit scale, 0 t0 255.
    This allows the use of web colour charts and the numerous
    colour tables and colour wheels available online.

    PixelGrid(NeoPixel)
    independent classes to avoid multiple levels of inheritance.

"""

from machine import Pin
from neopixel import NeoPixel


# selection of colours as rgb values
# see: https://docs.circuitpython.org/projects/led-animation/en/latest/
#      api.html#adafruit-led-animation-color


class PixelStrip(NeoPixel):
    """
        extend NeoPixel class with strip-related methods
    """

    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.n_pixels = n_pixels  # or use self.n

    def fill_strip(self, rgb_):
        """ fill all pixels with rgb colour """
        for index in range(self.n_pixels):
            self[index] = rgb_

    def fill_range(self, index_, count_, rgb_):
        """ fill count_ pixels with rgb_  """
        rgb = self.rgb_gamma[rgb_]
        for _ in range(count_):
            index_ %= self.n_pixels
            self[index_] = rgb
            index_ += 1

    def fill_range_c_list(self, index_, count_, rgb_list):
        """ fill count_ pixels with list of rgb values
            - n_rgb does not have to equal count_ """
        n_rgb = len(rgb_list)
        rgb_list = [self.rgb_gamma[rgb] for rgb in rgb_list]
        c_index = 0
        for _ in range(count_):
            index_ %= self.n_pixels
            c_index %= n_rgb
            self[index_] = rgb_list[c_index]
            index_ += 1
            c_index += 1

    def clear(self):
        """ set all pixels off """
        self.fill_strip((0, 0, 0))
        self.write()


class PixelGrid(NeoPixel):
    """ extend NeoPixel to support BTF-Lighting grid
        - grid is wired 'snake' style; coord_index dict corrects
    """

    def __init__(self, np_pin, n_cols_, n_rows_):
        self.n_pixels = n_cols_ * n_rows_
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels)
        self.np_pin = np_pin  # for logging/debug
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        self.c_r_dim = (self.n_cols, self.n_rows)
        self.coord_index = self.get_coord_index_dict()
        self.charset = None  # assigned externally from char_set

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

    def fill_grid(self, rgb_):
        """ fill grid with rgb_ colour """
        for index in range(self.n_pixels):
            self[index] = rgb_

    def fill_col(self, col, rgb_):
        """ fill col with rgb_ colour """
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb_

    def fill_row(self, row, rgb_):
        """ fill row with rgb_ colour """
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb_

    def fill_diagonal(self, rgb_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        if not mirror:
            for col in range(self.n_rows):
                self[self.coord_index[col, col]] = rgb_
        else:
            for col in range(self.n_rows):
                self[self.coord_index[self.max_col - col, col]] = rgb_

    def display_char(self, char_, rgb_):
        """ display a single character in rgb_ """
        if char_ in self.charset:
            char_grid = self.charset[char_]
            for row in range(self.n_rows):
                for col in range(self.n_cols):
                    self[self.coord_index[col, row]] = \
                        rgb_ if char_grid[row][col] else (0, 0, 0)
        else:
            self.fill_grid((0, 0, 0))

    def clear(self):
        """ set all pixels off """
        self.fill_grid((0, 0, 0))
        self.write()
