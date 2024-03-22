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
        - implicit conversion of colour-keys to RGB has been removed
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
        for index in range(self.n_pixels):
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

# helper methods

    async def fill_grid(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid(rgb_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        for index in range(self.n_pixels):
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
            for col in range(self.n_rows):
                self[self.coord_index[col, col]] = rgb_
        else:
            for col in range(self.n_rows):
                self[self.coord_index[self.n_rows - col, col]] = rgb_

    async def display_string(self, str_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        # rgb is set for the whole string
        for char in str_:
            self.set_list(self.charset[char], rgb_)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list(self.charset[char], (0, 0, 0))
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
        # attributes block-shift algorithm
        self.block_pixels = self.BLOCK_SIZE * self.BLOCK_SIZE
        self.seg_len = self.n_rows
        self.max_seg_index = (self.n_cols - 1) * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1

    def set_block_list(self, block_n, index_list_, rgb_):
        """ fill block_n index_list with rgb_ """
        offset = block_n * self.block_pixels
        for index in index_list_:
            self[index + offset] = rgb_

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
        for i in range(len(string_) - 1):
            self.set_block_list(0, self.charset[string_[i]], rgb_)
            self.set_block_list(1, self.charset[string_[i + 1]], rgb_)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid_left()
        await asyncio.sleep_ms(pause_ms)
