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
        - helper methods are examples or work-in-progress
    """

    BLOCK_SIZE = 8
    snake_diff = (15, 13, 11, 9, 7, 5, 3, 1)

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
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.block_cols = self.BLOCK_SIZE
        self.block_rows = self.BLOCK_SIZE
        self.max_col = n_cols_ - 1
        self.max_row = n_rows_ - 1
        self.max_block_col = self.block_cols - 1
        self.max_block_row = self.block_rows - 1
        self.coord_index = self.get_coord_index_dict()
        self.charset = self.get_char_indices(charset_file)
        self.set_grid = self.set_strip  # alias
        self.set_grid_rgb = self.set_strip_rgb  # alias

    def get_coord_index_dict(self):
        """ correct the grid 'snake' addressing scheme
            (c, r) coord -> list index
            - cols left to right, rows top to bottom
        """
        c_i_dict = {}
        max_row = self.max_row  # avoid repeated dict access
        for col in range(self.n_cols):
            is_odd = col % 2 == 1
            for row in range(self.n_rows):
                if is_odd:  # odd row
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

    def set_col(self, col, clr_, level_):
        """ fill col with rgb_ colour """
        rgb = self.cs.get_rgb(clr_, level_)
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb

    def set_col_rgb(self, col, rgb_):
        """ fill col with rgb_ colour """
        for row in range(self.n_rows):
            self[self.coord_index[col, row]] = rgb_

    def set_row(self, row, clr_, level_):
        """ fill row with rgb_ colour """
        rgb = self.cs.get_rgb(clr_, level_)
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb

    def set_row_rgb(self, row, rgb_):
        """ fill row with rgb_ colour """
        for col in range(self.n_cols):
            self[self.coord_index[col, row]] = rgb_

    def set_coord_list(self, coord_list_, clr_, level_):
        """ set a list of pixels by coords """
        # possibility coord_list_ could be empty
        if coord_list_:
            rgb = self.cs.get_rgb(clr_, level_)
            for c in coord_list_:
                self[self.coord_index[c]] = rgb

    def set_coord_list_rgb(self, coord_list_, rgb_):
        """ set a list of pixels by coords """
        if coord_list_:
            for c in coord_list_:
                self[self.coord_index[c]] = rgb_

# helper methods

    def set_block_rgb(self, block, index_list_, rgb_):
        """ fill 8x8 block  with rgb_ """
        offset = block * 64
        for index in index_list_:
            self[index + offset] = rgb_

    async def fill_grid(self, clr_, level_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid(clr_, level_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def fill_grid_rgb(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        self.set_grid_rgb(rgb_)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, clr_, level_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        rgb = self.cs.get_rgb(clr_, level_)
        for index in range(self.n):
            self[index] = rgb
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid(self, clr_, level_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """
        rgb = self.cs.get_rgb(clr_, level_)
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self[self.coord_index[(col, row)]] = rgb
                self.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols(self, clr_set, level_, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        n_colours = len(clr_set)
        for col in range(self.n_cols):
            self.set_col(col, clr_set[col % n_colours], level_)
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows(self, clr_set, level_, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        n_colours = len(clr_set)
        for row in range(self.n_rows):
            self.set_row(row, clr_set[row % n_colours], level_)
            self.write()
            await asyncio.sleep_ms(pause_ms)

    def set_diagonal(self, clr_, level_, mirror=False):
        """ fill diagonal with rgb_ colour
            - assumes n_cols >= n_rows
        """
        rgb = self.cs.get_rgb(clr_, level_)
        if not mirror:
            for col in range(self.block_cols):
                self[self.coord_index[col, col]] = rgb
        else:
            for col in range(self.block_cols):
                self[self.coord_index[self.max_block_col - col, col]] = rgb

    def set_char_rgb(self, block, char, rgb_):
        """ display a single character """
        self.set_block_rgb(block, self.charset[char], rgb_)

    async def shift_grid_left(self, pause_ms=20):
        """ coro: shift 1 col/iteration; write() each shift """
        for _ in range(8):  # block cols
            for index in range(120):  # all grid cols except last 1
                self[index] = self[index + self.snake_diff[index % 8]]
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fast_shift_grid_left(self, pause_ms=20):
        """ shift 2 cols/iteration; write() each shift """
        for _ in range(4):  # block cols // 2
            for index in range(112):  # all grid cols expcept last 2
                self[index] = self[index + 16]
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def display_string_rgb(self, str_, rgb_, pause_ms=1000):
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

    async def display_string_rgb_shift(self, string_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        max_index = len(string_) - 1
        for i in range(max_index):
            self.set_char_rgb(0, string_[i], rgb_)
            self.set_char_rgb(1, string_[i + 1], rgb_)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid_left()
        await asyncio.sleep_ms(pause_ms)
