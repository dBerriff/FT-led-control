# np_grid.py
""" Extends PixelStrip with 8x8 pixel grid attributes and methods """

import asyncio
from machine import Pin
import json
from np_strip import PixelStrip


class PixelGrid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
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

# helper methods

    async def fill_grid(self, rgb_, level_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid(rgb_, level_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, rgb_, level_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        rgb = self.get_rgb(rgb_, level_)
        for index in range(self.n):
            self[index] = rgb
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid(self, rgb_, level_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """
        rgb = self.get_rgb(rgb_, level_)
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self[self.coord_index[(col, row)]] = rgb
                self.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols(self, rgb_set, level_, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        n_colours = len(rgb_set)
        for col in range(self.n_cols):
            self.set_col(col, rgb_set[col % n_colours], level_)
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows(self, rgb_set, level_, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        n_colours = len(rgb_set)
        for row in range(self.n_rows):
            self.set_row(row, rgb_set[row % n_colours], level_)
            self.write()
            await asyncio.sleep_ms(pause_ms)

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

    async def display_string(self, str_, rgb_, level_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        # rgb is set for the whole string
        rgb = self.get_rgb(rgb_, level_)
        for char in str_:
            self.set_list_rgb(self.charset[char], rgb)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list_rgb(self.charset[char], (0, 0, 0))
            self.write()
