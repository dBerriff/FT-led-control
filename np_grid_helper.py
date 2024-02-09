# np_grid_helper.py
""" helper functions for PixelGrid class """

import asyncio


async def fill_grid(grid, rgb_, level_, pause_ms=20):
    """ coro: fill grid and display """
    grid.set_grid(rgb_, level_)
    grid.write()
    await asyncio.sleep_ms(pause_ms)


async def traverse_strip(npg, rgb_, level_, pause_ms=20):
    """ coro: fill each pixel in strip order """
    rgb = npg.get_rgb(rgb_, level_)
    for index in range(npg.n):
        npg[index] = rgb
        npg.write()
        await asyncio.sleep_ms(pause_ms)


async def traverse_grid(npg, rgb_, level_, pause_ms=20):
    """ coro: fill each pixel in grid coord order """
    rgb = npg.get_rgb(rgb_, level_)
    for row in range(npg.n_rows):
        for col in range(npg.n_cols):
            npg[npg.coord_index[(col, row)]] = rgb
            npg.write()
            await asyncio.sleep_ms(pause_ms)


async def fill_cols(npg, rgb_set, level_, pause_ms=20):
    """ coro: fill cols in order, cycling colours """
    n_colours = len(rgb_set)
    for col in range(npg.n_cols):
        npg.fill_col(col, rgb_set[col % n_colours], level_)
        npg.write()
        await asyncio.sleep_ms(pause_ms)


async def fill_rows(grid, rgb_set, level_, pause_ms=20):
    """ coro: fill rows in order, cycling colours """
    n_colours = len(rgb_set)
    for row in range(grid.n_rows):
        grid.fill_row(row, rgb_set[row % n_colours], level_)
        grid.write()
        await asyncio.sleep_ms(pause_ms)


async def display_string(npg_, str_, rgb_, level_, pause_ms=500):
    """ coro: display the letters in a string
        - set_char() overlays background
        - clear() grid first in this function
    """
    bkgrnd = 'black'
    npg_.clear()
    for char in str_:
        coords = npg_.get_char_coords(char)
        npg_.set_pixel_list(coords, rgb_, level_)
        npg_.write()
        await asyncio.sleep_ms(pause_ms)
        npg_.set_pixel_list(coords, bkgrnd, level_)
        npg_.write()
