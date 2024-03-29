# pixel_strip.py
"""
    Control WS2812E/NeoPixel lighting

    Encoding:
    User is expected to work with (R, G, B) 8-bit, or HSV values [0.0...1.0]

    Classes:

    PixelStrip
    Implements general application-related attributes and methods.
    Helper methods support specific use-cases.

    Notes:
    - set and encode methods do not write to pixels to allow for overlays
        -- write() must be called to display the output
"""

import asyncio
import json
from colour_space import ColourSpace
from ws2812 import Ws2812
from plasma_2040 import Plasma2040


class PixelStrip:
    """ extend Ws2812 for NeoPixel strip
        - MicroPython NeoPixel interface is matched as per MP documentation
        - RGBW (bpp) not currently implemented
        - __setitem__, set_pixel() and set_strip() implicitly set GRB grb_ order
        - some code is repeated to avoid additional method calls
    """

    def __init__(self, pin_, n_pixels_):
        self.pin = pin_  # for trace/debug
        self.n_pixels = n_pixels_
        self.chipset = Ws2812(pin_, n_pixels_)
        self.arr = self.chipset.arr
        self.cs = ColourSpace()

    def __len__(self):
        """ number of pixels """
        return self.n_pixels

    def set_pixel(self, index, raw):
        """ set pixel RGB; duplicates __setitem__() """
        self.arr[index] = raw

    def set_strip(self, raw):
        """ fill pixel strip with GRB """
        arr = self.arr  # avoid repeated dict lookup
        for i in range(self.n_pixels):
            arr[i] = raw

    def set_range(self, index_, count_, raw):
        """ fill count_ pixels with GRB  """
        arr = self.arr
        i = index_ % self.n_pixels
        for _ in range(count_):
            arr[i] = raw
            i += 1
            if i == self.n_pixels:
                i = 0

    def set_list(self, index_list_, raw):
        """ fill index_list pixels with GRB """
        arr = self.arr
        for i in index_list_:
            arr[i] = raw

    def clear_strip(self):
        """ set all pixels to 0 """
        arr = self.arr
        for i in range(self.n_pixels):
            arr[i] = 0

    def set_pixel_rgb(self, index, rgb_):
        """ set pixel RGB """
        self.set_pixel(index, self.chipset.encode_rgb(rgb_))

    def set_strip_rgb(self, rgb_):
        """ fill pixel strip with RGB """
        self.set_strip(self.chipset.encode_rgb(rgb_))

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with RGB  """
        self.set_range(index_, count_, self.chipset.encode_rgb(rgb_))

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with RGB """
        self.set_list(index_list_, self.chipset.encode_rgb(rgb_))


    def set_pixel_f(self, index, f_):
        """ set pixel RGB; duplicates __setitem__() """
        self.set_pixel(index, self.chipset.encode_f(f_))

    def set_strip_f(self, f_):
        """ fill pixel strip with RGB """
        self.set_strip(self.chipset.encode_f(f_))

    def set_range_f(self, index_, count_, f_):
        """ fill count_ pixels with RGB  """
        self.set_range(index_, count_, self.chipset.encode_f(f_))

    def set_list_f(self, index_list_, f_):
        """ fill index_list pixels with RGB """
        self.set_list(index_list_, self.chipset.encode_f(f_))

class Grid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
        - grid is wired 'snake' style;
            coord_index dict corrects by lookup
        - a block is an 8x8 area, intended for character display
        - implicit conversion of grb_-keys to RGB has been removed
        - helper methods are examples or work-in-progress
        - avoid, where straightforward, modulo (%) arithmetic for performance
    """

    @staticmethod
    def get_char_indices(file_name):
        """ return char pixel indices """
        with open(file_name, 'r') as f:
            retrieved = json.load(f)
        for ch in retrieved:
            retrieved[ch] = tuple(retrieved[ch])
        return retrieved

    def __init__(self, pin_, n_cols_, n_rows_, charset_file):
        self.n_pixels = n_cols_ * n_rows_
        super().__init__(pin_, self.n_pixels)
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

    def set_grid(self, rgb_):
        """ fill all grid pixels with rgb_ """
        grb = self.chipset.encode_rgb(rgb_)
        for index in range(self.n_pixels):
            self.arr[index] = grb

    def set_grid_grb(self, grb_):
        """ fill all grid pixels with grb_ """
        for index in range(self.n_pixels):
            self.arr[index] = grb_

    def set_col(self, col, rgb_):
        """ fill col with rgb_ """
        grb = self.chipset.encode_rgb(rgb_)
        for row in range(self.n_rows):
            self.arr[self.coord_index[col, row]] = grb

    def set_col_grb(self, col, grb_):
        """ fill col with grb_ """
        for row in range(self.n_rows):
            self.arr[self.coord_index[col, row]] = grb_

    def set_row(self, row, rgb_):
        """ fill row with rgb_ grb_ """
        grb = self.chipset.encode_rgb(rgb_)
        for col in range(self.n_cols):
            self.arr[self.coord_index[col, row]] = grb

    def set_row_grb(self, row, grb_):
        """ fill row with rgb_ grb_ """
        for col in range(self.n_cols):
            self.arr[self.coord_index[col, row]] = grb_

    def set_coord_list(self, coord_list_, rgb_):
        """ set a list of pixels by coords """
        grb = self.chipset.encode_rgb(rgb_)
        if coord_list_:  # could be empty
            for c in coord_list_:
                self.arr[self.coord_index[c]] = grb

# helper methods

    async def fill_grid(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        grb = self.chipset.encode_rgb(rgb_)
        self.set_grid_grb(grb)
        self.chipset.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        grb = self.chipset.encode_rgb(rgb_)
        for index in range(self.n_pixels):
            self.arr[index] = grb
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """
        grb = self.chipset.encode_rgb(rgb_)
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self.arr[self.coord_index[col, row]] = grb
                self.chipset.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols(self, rgb_set, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        grb_set = []
        for c in rgb_set:
            grb_set.append(self.chipset.encode_rgb(c))
        n_colours = len(grb_set)
        for col in range(self.n_cols):
            self.set_col_grb(col, grb_set[col % n_colours])
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows(self, rgb_set, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        grb_set = []
        for c in rgb_set:
            grb_set.append(self.chipset.encode_rgb(c))
        n_colours = len(grb_set)
        for row in range(self.n_rows):
            self.set_row_grb(row, grb_set[row % n_colours])
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)

    def set_diagonal(self, rgb_, mirror=False):
        """ fill diagonal with rgb_ grb_
            - assumes n_cols >= n_rows
        """
        grb = self.chipset.encode_rgb(rgb_)
        if mirror:
            for col in range(self.n_rows):
                self.arr[self.coord_index[self.max_row - col, col]] = grb
        else:
            for col in range(self.n_rows):
                self.arr[self.coord_index[col, col]] = grb

    async def display_string(self, str_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        grb = self.chipset.encode_rgb(rgb_)
        # grb is set for the whole string
        for char in str_:
            self.set_list(self.charset[char], grb)
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list(self.charset[char], 0)
            self.chipset.write()


class BlockGrid(Grid):
    """ extend Grid to support block-to-block left shift
        - right-hand virtual block added for char shift-in
        - this version assumes horizontal blocks
    """

    BLOCK_SIZE = 8

    def __init__(self, pin_, n_cols_, n_rows_, charset_file):
        # add virtual block to end of grid
        self.n_cols = n_cols_ + self.BLOCK_SIZE
        super().__init__(pin_, self.n_cols, n_rows_, charset_file)
        # attributes for block-shift algorithm
        self.block_pixels = self.BLOCK_SIZE * self.BLOCK_SIZE
        self.seg_len = self.n_rows
        self.max_seg_index = (self.n_cols - 1) * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1

    def set_block_list(self, block_n, index_list_, grb_):
        """ fill block_n index_list with rgb_ """
        offset = block_n * self.block_pixels
        for index in index_list_:
            self.arr[index + offset] = grb_

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
                    self.chipset.arr[col_index] = self.chipset.arr[col_index + offset]
                    col_index += 1
                    offset -= 2
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)

    async def display_string_shift(self, string_, rgb_, pause_ms=1000):
        """
            coro: display letters in a string, shifting in from right
            - block 1 is usually a virtual block
        """
        grb = self.chipset.encode_rgb(rgb_)
        for i in range(len(string_) - 1):
            self.set_block_list(0, self.charset[string_[i]], grb)
            self.set_block_list(1, self.charset[string_[i + 1]], grb)
            self.chipset.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid_left()
        await asyncio.sleep_ms(pause_ms)


async def main():
    """ coro: test NeoPixel strip helper functions """

    # Pimoroni Plasma 2040 is hardwired to GPIO 15
    n_pixels = 30
    board = Plasma2040()
    chipset = Ws2812(board.DATA, n_pixels)
    ps = PixelStrip(board.DATA, n_pixels)
    cs = ColourSpace()
    level = 128

    rgb_u24 = chipset.encode_rgb(
        cs.get_rgb_lg('orange', level))
    print(rgb_u24)

    # single pixel
    ps.set_pixel(8, rgb_u24)
    ps.chipset.write()
    await asyncio.sleep_ms(2_000)
    ps.clear_strip()
    ps.chipset.write()
    await asyncio.sleep_ms(200)

    # whole strip
    ps.set_strip(rgb_u24)
    ps.chipset.write()
    await asyncio.sleep_ms(2_000)
    ps.clear_strip()
    ps.chipset.write()
    await asyncio.sleep_ms(200)

    # range
    ps.set_range(26, 8, rgb_u24)
    ps.chipset.write()
    await asyncio.sleep_ms(2_000)
    ps.clear_strip()
    ps.chipset.write()
    await asyncio.sleep_ms(200)

    # list
    ps.set_list([0, 2, 4, 6, 8], rgb_u24)
    ps.chipset.write()
    await asyncio.sleep_ms(2_000)
    ps.clear_strip()
    ps.chipset.write()
    await asyncio.sleep_ms(200)

    for angle in range(0, 360, 60):
        rgb_u8 = cs.hsv_rgb_u8(angle/360, 0.9, 0.25)
        print(angle, rgb_u8)
        rgb_u24 = chipset.encode_rgb(
            cs.get_rgb_g(rgb_u8))

        # single pixel
        ps.set_pixel(8, rgb_u24)
        ps.chipset.write()
        await asyncio.sleep_ms(2_000)
        ps.clear_strip()
        ps.chipset.write()
        await asyncio.sleep_ms(200)

        # whole strip
        ps.set_strip(rgb_u24)
        ps.chipset.write()
        await asyncio.sleep_ms(2_000)
        ps.clear_strip()
        ps.chipset.write()
        await asyncio.sleep_ms(200)

        # range
        ps.set_range(26, 8, rgb_u24)
        ps.chipset.write()
        await asyncio.sleep_ms(2_000)
        ps.clear_strip()
        ps.chipset.write()
        await asyncio.sleep_ms(200)

        # list
        ps.set_list([0, 2, 4, 6, 8], rgb_u24)
        ps.chipset.write()
        await asyncio.sleep_ms(2_000)
        ps.clear_strip()
        ps.chipset.write()
        await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
