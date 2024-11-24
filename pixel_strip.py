# pixel_strip.py
"""
    Control WS2812E/NeoPixel lighting

    Encoding:
    User: RGB(W) tuple of u8 values, or HSV values as [0.0...1.0]
    Internal: colour as u24 word, target-dependent

    Classes:
    PixelStrip:
    General application-related attributes and methods.
    Helper methods support specific use-cases.
    Grid:
    Display on square grid wired as 'snake' strip
    BlockGrid:
    Display on multiple square grids (blocks)
    Adds method to shift characters in from right

    Notes:
    - set methods do not write to pixels to allow for overlays
        -- write() must be called to display the output
        -- pixel drivers can require a pause between writes
"""

import asyncio
import json
from colour_space import ColourSpace


class PixelStrip:
    """ implement general pixel strip methods
        driver implements board_ and strip-logic attributes and methods
        - MicroPython NeoPixel interface is matched as per MP documentation
        - some code is repeated to avoid nested method calls
        - method local variables are used where this avoids repeated dict lookup
    """

    def __init__(self, driver_, n_pixels_):
        self.driver = driver_
        self.n_pixels = n_pixels_
        self.driver.set_n_pixels(n_pixels_)
        self.driver.set_active()
        self.arr = self.driver.arr
        self.encode_rgb = self.driver.encode_rgb
        self.write = self.driver.write
        self.cs = ColourSpace()

    # match MP NeoPixel interface with len, setitem and getitem

    def __len__(self):
        """ number of pixels """
        return self.n_pixels

    def __setitem__(self, index, colour_u24):
        """ set array item """
        self.arr[index] = colour_u24

    def __getitem__(self, index):
        """ get array item """
        return self.arr[index]

    # class methods

    def clear_strip(self):
        """ set all pixels off """
        arr_ = self.arr
        for i in range(self.n_pixels):
            arr_[i] = 0
        self.write()

    def set_pixel(self, index, colour_u24):
        """ set single pixel to 24-bit RGB (duplicates __setitem__) """
        self.arr[index] = colour_u24

    def set_strip(self, colour_u24):
        """ fill pixel with RGB """
        arr_ = self.arr
        for i in range(self.n_pixels):
            arr_[i] = colour_u24

    def set_range(self, index_, count_, colour_u24):
        """ fill count_ pixels """
        arr_ = self.arr
        i = index_ % self.n_pixels
        for _ in range(count_):
            arr_[i] = colour_u24
            i += 1
            if i == self.n_pixels:
                i = 0

    def set_list(self, index_list_, colour_u24):
        """ fill index_list pixels """
        arr_ = self.arr
        for i in index_list_:
            arr_[i] = colour_u24

    def set_pixel_rgb(self, index, rgb_):
        """ set pixel by RGB tuple """
        self.set_pixel(index, self.encode_rgb(rgb_))

    def set_strip_rgb(self, rgb_):
        """ fill pixel strip with RGB tuple """
        self.set_strip(self.encode_rgb(rgb_))

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with RGB tuple  """
        self.set_range(index_, count_, self.encode_rgb(rgb_))

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with RGB tuple """
        self.set_list(index_list_, self.encode_rgb(rgb_))


class Grid(PixelStrip):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
        - grid is wired 'snake' style; coord_index dict corrects
    """

    @staticmethod
    def get_char_indices(file_name):
        """ return char pixel indices """
        try:
            with open(file_name, 'r') as f:
                retrieved = json.load(f)
        except OSError:
            print(f'File: {file_name} could not be opened for reading')
            return None
        for ch in retrieved:
            retrieved[ch] = tuple(retrieved[ch])
        return retrieved

    def __init__(self, driver_, n_cols_, n_rows_, charset_file):
        super().__init__(driver_, n_cols_ * n_rows_)
        self.driver = driver_
        self.n_cols = n_cols_
        self.n_rows = n_rows_
        self.charset = self.get_char_indices(charset_file)
        self.max_col = self.n_cols - 1
        self.max_row = self.n_rows - 1
        # build dict: (col, row) to pixel-index conversion
        self.coord_index = self.build_c_i_dict()

    def build_c_i_dict(self):
        """ correct the grid 'snake' addressing scheme
            (c, r) coord -> list index
            - cols left to right, rows top to bottom
        """
        c_i_dict = dict()
        max_row = self.max_row
        even = False  # toggle True for row 0
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

    def set_grid_rgb(self, rgb_):
        """ fill all grid pixels with rgb_ """
        clr = self.encode_rgb(rgb_)
        for index in range(self.n_pixels):
            self.arr[index] = clr

    def set_grid(self, colour_u24):
        """ fill all grid pixels with colour_u24 """
        for index in range(self.n_pixels):
            self.arr[index] = colour_u24

    def set_col_rgb(self, col, rgb_):
        """ fill cols with rgb_ """
        clr = self.encode_rgb(rgb_)
        for row in range(self.n_rows):
            self.arr[self.coord_index[col, row]] = clr

    def set_col(self, col, colour_u24):
        """ fill cols with colour_u24 """
        for row in range(self.n_rows):
            self.arr[self.coord_index[col, row]] = colour_u24

    def set_row_rgb(self, row, rgb_):
        """ fill rows with colour_u24 """
        clr = self.encode_rgb(rgb_)
        for col in range(self.n_cols):
            self.arr[self.coord_index[col, row]] = clr

    def set_row(self, row, colour_u24):
        """ fill rows with colour_u24 """
        for col in range(self.n_cols):
            self.arr[self.coord_index[col, row]] = colour_u24

    def set_coord_list_rgb(self, coord_list_, rgb_):
        """ set a list of pixels by coords """
        clr = self.encode_rgb(rgb_)
        if coord_list_:  # could be empty
            for c in coord_list_:
                self.arr[self.coord_index[c]] = clr

# helper methods

    async def fill_grid_rgb(self, rgb_, pause_ms=20):
        """ coro: fill grid and display """
        clr = self.encode_rgb(rgb_)
        self.set_grid(clr)
        self.write()
        await asyncio.sleep_ms(pause_ms)

    async def traverse_strip_rgb(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in strip order """
        clr = self.encode_rgb(rgb_)
        for index in range(self.n_pixels):
            self.arr[index] = clr
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def traverse_grid_rgb(self, rgb_, pause_ms=20):
        """ coro: fill each pixel in grid coord order """
        clr = self.encode_rgb(rgb_)
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                self.arr[self.coord_index[col, row]] = clr
                self.write()
                await asyncio.sleep_ms(pause_ms)

    async def fill_cols_rgbset(self, rgb_set, pause_ms=20):
        """ coro: fill cols in order, cycling colours """
        clr_set = []
        for c in rgb_set:
            clr_set.append(self.encode_rgb(c))
        n_colours = len(clr_set)
        for col in range(self.n_cols):
            self.set_col(col, clr_set[col % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def fill_rows_rgbset(self, rgb_set, pause_ms=20):
        """ coro: fill rows in order, cycling colours """
        clr_set = []
        for c in rgb_set:
            clr_set.append(self.encode_rgb(c))
        n_colours = len(clr_set)
        for row in range(self.n_rows):
            self.set_row(row, clr_set[row % n_colours])
            self.write()
            await asyncio.sleep_ms(pause_ms)

    def set_diagonal_rgb(self, rgb_, mirror=False):
        """ fill diagonal with rgb_ colour_u24
            - assumes n_cols >= n_rows
        """
        clr = self.encode_rgb(rgb_)
        if mirror:
            for col in range(self.n_rows):
                self.arr[self.coord_index[self.max_row - col, col]] = clr
        else:
            for col in range(self.n_rows):
                self.arr[self.coord_index[col, col]] = clr

    async def display_string_rgb(self, str_, rgb_, pause_ms=1000):
        """ coro: display the letters in a string
            - set_char() overlays background
        """
        clr = self.encode_rgb(rgb_)
        # colour_u24 is set for the whole string
        for char in str_:
            self.set_list(self.charset[char], clr)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self.set_list(self.charset[char], 0)
            self.write()
            await asyncio.sleep_ms(1)


class BlockGrid(Grid):
    """ !!! not yet fully functional
        extend Grid to support block-to-block left shift
        - this version assumes horizontal blocks
        - optional: include a virtual right-hand block for char shift-in
    """

    def __init__(self, driver_, n_b_cols, n_b_rows, n_blocks, charset_file):
        self.block_cols = n_b_cols
        self.n_cols = n_b_cols * n_blocks
        self.n_rows = n_b_rows
        self.n_blocks = n_blocks
        super().__init__(driver_, self.n_cols, self.n_rows, charset_file)
        # attributes for block-shift algorithm
        self.block_pixels = n_b_cols * n_b_rows
        self.seg_len = self.n_rows
        self.max_seg_index = (self.n_cols - 1) * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1

    def set_block_list(self, block_n, index_list_, clr):
        """ fill block_n index_list with colour_u24 """
        offset = block_n * self.block_pixels
        for index in index_list_:
            self.arr[index + offset] = clr

    async def shift_grid(self, pause_ms=20):
        """
            coro: shift left 1 col/iteration; write() each shift
            - shift_offset is for adjacent block-cols segments
            - shift array values direct: avoid decode/encode
        """
        for _ in range(self.block_cols):  # shift left by block columns
            for col_index in range(0, self.max_seg_index, self.n_rows):
                offset = self.shift_offset
                while offset > 0:
                    self.arr[col_index] = self.arr[col_index + offset]
                    col_index += 1
                    offset -= 2
            self.write()
            await asyncio.sleep_ms(pause_ms)

    async def shift_string_rgb(self, string_, rgb_, pause_ms=1000):
        """
            coro: display letters in a string, shifting in from right
            - block 1 is usually a virtual block
        """
        clr = self.encode_rgb(rgb_)
        for i in range(len(string_) - 1):
            self.set_block_list(0, self.charset[string_[i]], clr)
            self.set_block_list(1, self.charset[string_[i + 1]], clr)
            self.write()
            await asyncio.sleep_ms(pause_ms)
            await self.shift_grid()
        await asyncio.sleep_ms(pause_ms)
