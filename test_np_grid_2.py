# test_np_grid.py

""" test LED- and NeoPixel-related classes
    - 'block' is an 8x8 square in the grid
    - 'grid' is the whole grid including any virtual blocks
"""

import asyncio
from np_grid import PixelGrid

snake_diff = (15, 13, 11, 9, 7, 5, 3, 1)

def set_block_rgb(npg, block, index_list_, rgb_):
    """ fill 8x8 block pixels with rgb_ """
    offset = block * 64
    for index in index_list_:
        npg[index + offset] = rgb_


def set_char_rgb(npg, block, char, rgb_):
    """ display a single character """
    set_block_rgb(npg, block, npg.charset[char], rgb_)


async def shift_grid_left(npg, shift_pause_ms=0):
    """ coro: shift a grid, 1 column/iteration, to the left
              and write() each shift
        - final column in the grid is not filled
        - final grid is (usually) virtual so a char can be shifted in
    """

    for _ in range(8):  # 8 shifts
        for c_i in range(0, 120, 8):  # shift all columns except last
            for r in range(8):
                index = c_i + r
                npg[index] = npg[index + snake_diff[r]]
        npg.write()
        await asyncio.sleep_ms(shift_pause_ms)

async def fast_shift_grid_left(npg, shift_pause_ms=0):
    """ coro: shift a grid, 2 columns/iteration, to the left 
              and write() each shift
        - 2 col shift avoids strip-order index computation
        - final column in the grid is not filled
        - final grid is (usually) virtual so a char can be shifted in
    """
    for _ in range(4):  # block cols // 2
        for c_i in range(0, 112, 16):
            for r in range(16):
                index = c_i + r
                npg[index] = npg[index + 16]
        npg.write()
        await asyncio.sleep_ms(shift_pause_ms)

async def display_string(npg, string_, rgb_, pause_ms=1000):
    """ coro: display the letters in a string
        - set_char() overlays background
    """
    max_index = len(string_) - 1
    for i in range(max_index):
        set_char_rgb(npg, 0, string_[i], rgb_)
        set_char_rgb(npg, 1, string_[i + 1], rgb_)
        npg.write()
        await asyncio.sleep_ms(1000)
        await shift_grid_left(npg)
    await asyncio.sleep_ms(1000)

async def fast_display_string(npg, string_, rgb_, pause_ms=1000):
    """ coro: display the letters in a string
        - set_char() overlays background
    """
    max_index = len(string_) - 1
    for i in range(max_index):
        set_char_rgb(npg, 0, string_[i], rgb_)
        set_char_rgb(npg, 1, string_[i + 1], rgb_)
        npg.write()
        await asyncio.sleep_ms(1000)
        await fast_shift_grid_left(npg)
    await asyncio.sleep_ms(1000)

async def main():
    """ coro: test NeoPixel grid helper functions """

    pin_number = 27
    npg = PixelGrid(
        pin_number, n_cols_=16, n_rows_=8, cs_file='5x7.json')
    level = 64
    rgb = npg.get_rgb('dark_orange', level)

    # test character shift-left
    blocks = 2
    n_columns = 8 * blocks
    n_rows = 8
    # avoid repeatedly recreating this list

    await display_string(npg, ' This is a test.', rgb)
    npg.clear()
    await asyncio.sleep_ms(1000)
    await fast_display_string(npg, ' This is a test.', rgb)
    npg.clear()
if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
