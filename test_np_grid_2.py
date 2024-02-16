# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid


def set_block_rgb(npg, block, index_list_, rgb_):
    """ fill 8x8 block pixels with rgb_ """
    offset = block * 64
    for index in index_list_:
        npg[index + offset] = rgb_


def set_char_rgb(npg, block, char, rgb_):
    """ display a single character """
    set_block_rgb(npg, block, npg.charset[char], rgb_)


async def shift_grid_left(npg, shift_index_list_, shift_pause_ms=20):
    """ coro: shift the columns of a grid to the left
            and write() each shift
        - diff is for a snake-order strip
        - final column in the grid is not filled
        - final grid is (usually) virtual so a char can be shifted in
    """
    # block_columns = 8
    for _ in range(8):
        for index in shift_index_list_:
            diff = 15
            while diff > 0:
                npg[index] = npg[index + diff]
                index += 1
                diff -= 2
        npg.write()
        await asyncio.sleep_ms(shift_pause_ms)

async def fast_shift_grid_left(npg, shift_pause_ms=20):
    """ coro: shift the columns of a grid to the left 2 columns
            and write() each shift
        - double-step avoids strip-order index computation
        - final column in the grid is not filled
        - final grid is (usually) virtual so a char can be shifted in
    """
    # block_columns = 8
    for _ in range(0, 8, 2):
        for col in range(0, 14, 2):
            index = col * 8
            for i in range(index, index + 16):
                npg[i] = npg[i + 16]
        npg.write()
        await asyncio.sleep_ms(shift_pause_ms)

async def display_string(npg, string_, rgb_, shift_index_list_, pause_ms=1000):
    """ coro: display the letters in a string
        - set_char() overlays background
    """
    max_index = len(string_) - 1
    for i in range(max_index):
        set_char_rgb(npg, 0, string_[i], rgb_)
        set_char_rgb(npg, 1, string_[i + 1], rgb_)
        npg.write()
        await asyncio.sleep_ms(1000)
        await shift_grid_left(npg, shift_index_list_)
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
    shift_indices = []
    # fill all except last column
    for i in range(0, n_rows * (n_columns - 1), n_rows):
        shift_indices.append(i)

    await display_string(npg, ' This is a test.', rgb, shift_indices)
    npg.clear()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
