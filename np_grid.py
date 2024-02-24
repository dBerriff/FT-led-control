# np_grid.py
""" Helper methods for PixelStrip with 8x8 pixel grid attributes and methods """

import asyncio
from machine import Pin
import json
from pio_ws2812 import Ws2812Strip as PixelStrip
from colour_space import ColourSpace
import time


class PixelGrid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
        - grid is wired 'snake' style;
            coord_index dict corrects by lookup
        - a block is an 8x8 area, intended for character display
        - implicit conversion of colour-keys to RGB has been removed
        - helper methods are examples or work-in-progress
    """

    BLOCK_SIZE = 8

    @staticmethod
    def get_char_indices(file_name):
        """ return char pixel indices """
        with open(file_name, 'r') as f:
            retrieved = json.load(f)
        for ch in retrieved:
            retrieved[ch] = tuple(retrieved[ch])
        return retrieved

    def __init__(self, np_pin, n_cols_, n_rows_, charset_file):
        self.n_pixels = (n_cols_ + self.BLOCK_SIZE) * n_rows_  # add virtual block
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels)
        self.grid_pixels = n_cols_ * n_rows_
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        # set up grid blocks for chars
        self.block_cols = self.BLOCK_SIZE
        self.block_rows = self.BLOCK_SIZE  # not used
        self.max_block_col = self.BLOCK_SIZE - 1
        self.max_block_row = self.BLOCK_SIZE - 1
        self.n_blocks = n_cols_ // self.BLOCK_SIZE
        self.v_blocks = self.n_blocks + 1  # virtual block for left-shift
        self.max_v_col = self.v_blocks * self.BLOCK_SIZE - 1  # no shift into final col
        # segments for block-shift algorithm - strip order
        self.seg_len = self.n_rows
        self.max_seg_index = self.max_v_col * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1
        # dict for (col, row) to pixel-index conversion
        self.coord_index = self.get_coord_index_dict()
        # character set as pixel-index lists
        self.charset = self.get_char_indices(charset_file)

    def get_coord_index_dict(self):
        """ correct the grid 'snake' addressing scheme
            (c, r) coord -> list index
            - cols left to right, rows top to bottom
        """
        c_i_dict = {}
        max_row = self.max_row  # avoid repeated dict access
        for col in range(self.n_cols):
            if col % 2 == 1:  # odd
                for row in range(self.n_rows):
                    c_i_dict[col, row] = col * self.n_rows + max_row - row
            else:
                for row in range(self.n_rows):
                    c_i_dict[col, row] = col * self.n_rows + row
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

    def set_grid(self, rgb_):
        """ fill all grid pixels with rgb colour """
        for index in range(self.grid_pixels):
            self[index] = rgb_

    def set_col(self, col, rgb_):
        """ fill col with rgb_ colour """
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb_

    def set_row(self, row, rgb_):
        """ fill row with rgb_ colour """
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb_

    def set_coord_list(self, coord_list_, rgb_):
        """ set a list of pixels by coords """
        if coord_list_:  # could be empty
            for c in coord_list_:
                self[self.coord_index[c]] = rgb_

    def set_block_list(self, block, index_list_, rgb_):
        """ fill 8x8 block index_list with rgb_ """
        offset = block * 64
        for index in index_list_:
            self[index + offset] = rgb_

# helper methods

    async def fill_grid(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid(rgb_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        for index in range(self.grid_pixels):
            self[index] = rgb_
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """

        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self[self.coord_index[(col, row)]] = rgb_
                self.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols(self, rgb_set, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        n_colours = len(rgb_set)
        for col in range(self.n_cols):
            self.set_col(col, rgb_set[col % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows(self, rgb_set, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        n_colours = len(rgb_set)
        for row in range(self.n_rows):
            self.set_row(row, rgb_set[row % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    def set_diagonal(self, rgb_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        if not mirror:
            for col in range(self.block_cols):
                self[self.coord_index[col, col]] = rgb_
        else:
            for col in range(self.block_cols):
                self[self.coord_index[self.max_block_col - col, col]] = rgb_

    async def display_string(self, str_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        # rgb is set for the whole string
        for char in str_:
            self.set_list_rgb(self.charset[char], rgb_)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list_rgb(self.charset[char], (0, 0, 0))
            self.write()

    async def shift_grid_left(self, pause_ms=20):
        """ coro: shift 1 col/iteration; write() each shift
            - not fully parameterised
            - indices for 8x8 blocks
            - offset for adjacent 8-element segments
        """
        for _ in range(self.block_cols):  # shift left into block
            for index in range(0, self.max_seg_index, self.seg_len):
                offset = self.shift_offset
                while offset > 0:
                    self.arr[index] = self.arr[index + offset]
                    index += 1
                    offset -= 2
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def display_string_shift(self, string_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        max_index = len(string_) - 1
        for i in range(max_index):
            self.set_block_list(0, self.charset[string_[i]], rgb_)
            self.set_block_list(1, self.charset[string_[i + 1]], rgb_)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid_left()
        await asyncio.sleep_ms(pause_ms)
