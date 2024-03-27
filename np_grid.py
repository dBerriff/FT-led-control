# np_grid.py
""" Helper methods for PixelStrip with 8x8 pixel grid attributes and methods """

import asyncio
from machine import Pin
import json
from pio_ws2812 import Ws2812Strip


class Ws2812Grid(Ws2812Strip):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
        - grid is wired 'snake' style;
            coord_index dict corrects by lookup
        - a block is an 8x8 area, intended for character display
        - implicit conversion of grb_-keys to RGB has been removed
        - helper methods are examples or work-in-progress
    """

    @staticmethod
    def get_char_indices(file_name):
        """ return char pixel indices """
        with open(file_name, 'r') as f:
            retrieved = json.load(f)
        for ch in retrieved:
            retrieved[ch] = tuple(retrieved[ch])
        return retrieved

    def __init__(self, np_pin, n_cols_, n_rows_, charset_file):
        self.n_pixels = n_cols_ * n_rows_
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels)
        # character set as pixel-index lists
        self.charset = self.get_char_indices(charset_file)
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        # dict for (col, row) to pixel-index conversion
        self.coord_index = self.get_coord_index_dict()

    def get_coord_index_dict(self):
        """ correct the grid 'snake' addressing scheme
            (c, r) coord -> list index
            - cols left to right, rows top to bottom
        """
        c_i_dict = {}
        max_row = self.max_row  # avoid repeated dict access
        even = False  # row 0 is even
        for col in range(self.n_cols):
            base = col * self.n_rows
            even = not even
            if even:
                for row in range(self.n_rows):
                    c_i_dict[col, row] = base + row
            else:
                for row in range(self.n_rows):
                    c_i_dict[col, row] = base + max_row - row
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
        """ fill all grid pixels with rgb grb_ """
        grb = self.encode_grb(rgb_)
        for index in range(self.n_pixels):
            self[index] = grb

    def set_col(self, col, rgb_):
        """ fill col with rgb_ """
        self.set_col_grb(self.encode_grb(rgb_))

    def set_col_grb(self, col, grb_):
        """ fill col with rgb_ """
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = grb_

    def set_row(self, row, rgb_):
        """ fill row with rgb_ grb_ """
        self.set_row_grb(self.encode_grb(rgb_))

    def set_row_grb(self, row, grb_):
        """ fill row with rgb_ grb_ """
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = grb_

    def set_coord_list(self, coord_list_, rgb_):
        """ set a list of pixels by coords """
        grb = self.encode_grb(rgb_)
        if coord_list_:  # could be empty
            for c in coord_list_:
                self[self.coord_index[c]] = grb

# helper methods

    async def fill_grid(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid(rgb_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        grb = self.encode_grb(rgb_)
        for index in range(self.n_pixels):
            self[index] = grb
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """
        grb = self.encode_grb(rgb_)
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self[self.coord_index[col, row]] = grb
                self.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols(self, rgb_set, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        grb_set = []
        for c in rgb_set:
            grb_set.append(self.encode_grb(c))
        n_colours = len(grb_set)
        for col in range(self.n_cols):
            self.set_col_grb(col, grb_set[col % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows(self, rgb_set, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        grb_set = []
        for c in rgb_set:
            grb_set.append(self.encode_grb(c))
        n_colours = len(grb_set)
        for row in range(self.n_rows):
            self.set_row_grb(row, grb_set[row % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    def set_diagonal(self, rgb_, mirror=False):
        """ fill diagonal with rgb_ grb_
            - assumes n_cols >= n_rows
        """
        grb = self.encode_grb(rgb_)
        if mirror:
            for col in range(self.n_rows):
                self[self.coord_index[self.max_row - col, col]] = grb
        else:
            for col in range(self.n_rows):
                self[self.coord_index[col, col]] = grb

    async def display_string(self, str_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        grb = self.encode_grb(rgb_)
        # rgb is set for the whole string
        for char in str_:
            self.set_list_grb(self.charset[char], grb)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list_grb(self.charset[char], 0)
            self.write()


class BlockGrid(Ws2812Grid):
    """ extend Ws2812Grid to support block-to-block left shift
        - right-hand virtual block added for char shift-in
        - this version assumes horizontal blocks
    """

    BLOCK_SIZE = 8

    def __init__(self, np_pin, n_cols_, n_rows_, charset_file):
        # add virtual block to end of grid
        self.n_cols = n_cols_ + self.BLOCK_SIZE
        super().__init__(Pin(np_pin, Pin.OUT), self.n_cols, n_rows_, charset_file)
        # attributes for block-shift algorithm
        self.block_pixels = self.BLOCK_SIZE * self.BLOCK_SIZE
        self.seg_len = self.n_rows
        self.max_seg_index = (self.n_cols - 1) * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1

    def set_block_list(self, block_n, index_list_, grb_):
        """ fill block_n index_list with rgb_ """
        offset = block_n * self.block_pixels
        for index in index_list_:
            self[index + offset] = grb_

    async def shift_grid_left(self, pause_ms=20):
        """
            coro: shift left 1 col/iteration; write() each shift
            - shift_offset is for adjacent block-cols segments
            - shift array values direct: avoid decode/encode
        """
        for _ in range(self.BLOCK_SIZE):  # shift left by block columns
            for col_index in range(0, self.max_seg_index, self.n_rows):
                offset = self.shift_offset
                while offset > 0:
                    self.arr[col_index] = self.arr[col_index + offset]
                    col_index += 1
                    offset -= 2
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def display_string_shift(self, string_, rgb_, pause_ms=1000):
        """
            coro: display letters in a string, shifting in from right
            - block 1 is usually a virtual block
        """
        grb = self.encode_grb(rgb_)
        for i in range(len(string_) - 1):
            self.set_block_list(0, self.charset[string_[i]], grb)
            self.set_block_list(1, self.charset[string_[i + 1]], grb)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid_left()
        await asyncio.sleep_ms(pause_ms)
