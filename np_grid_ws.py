# np_grid.py
""" Helper methods for PixelStrip with 8x8 pixel grid attributes and methods """

import asyncio
from machine import Pin
from np_grid import PixelGrid


class BlockGrid(PixelGrid):
    """ extend NeoPixel to support BTF-Lighting 8x8 grid
        - grid is wired 'snake' style;
            coord_index dict corrects by lookup
        - a block is an 8x8 area, intended for character display
        - implicit conversion of colour-keys to RGB has been removed
        - helper methods are examples or work-in-progress
    """

    BLOCK_SIZE = 8

    def __init__(self, np_pin, n_cols_, n_rows_, charset_file):
        self.n_cols = n_cols_ + self.BLOCK_SIZE  # virtual block
        super().__init__(Pin(np_pin, Pin.OUT), n_cols_, n_rows_, charset_file)
        self.grid_pixels = n_cols_ * n_rows_
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

    def set_block_list(self, block, index_list_, rgb_):
        """ fill 8x8 block index_list with rgb_ """
        offset = block * 64
        for index in index_list_:
            self[index + offset] = rgb_

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
