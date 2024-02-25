# np_grid.py
""" Helper methods for PixelStrip with 8x8 pixel grid attributes and methods """

import asyncio
from machine import Pin
from np_grid import Ws2812Grid


class BlockGrid(Ws2812Grid):
    """ extend Ws2812Grid to support block-to-block left shift
        - right-hand virtual block can be added for char shift-in
        - this version assumes horizontal blocks
    """

    BLOCK_SIZE = 8

    def __init__(self, np_pin, n_cols_, n_rows_, charset_file):
        # add virtual block to end of grid
        self.n_cols = n_cols_ + self.BLOCK_SIZE
        super().__init__(Pin(np_pin, Pin.OUT), n_cols_, n_rows_, charset_file)
        # attributes block-shift algorithm
        self.block_pixels = self.BLOCK_SIZE * self.BLOCK_SIZE
        self.seg_len = self.n_rows
        self.max_seg_index = (self.n_cols - 1) * self.seg_len
        self.shift_offset = 2 * self.n_rows - 1

    def set_block_list(self, block_i, index_list_, rgb_):
        """ fill block n index_list with rgb_ """
        offset = block_i * self.block_pixels
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
