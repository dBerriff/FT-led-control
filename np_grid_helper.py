# np_grid_helper.py
""" helper functions for PixelGrid class """

import asyncio


async def fill_grid(npg, rgb_, level_, pause_ms=20):
    """ coro: fill grid and display """
    npg.set_grid(rgb_, level_)
    npg.write()
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


async def display_string(npg, str_, rgb_, level_, pause_ms=1000):
    """ coro: display the letters in a string from index list
        - set_char() overlays background
    """
    # rgb is set for the whole string
    rgb = npg.get_rgb(rgb_, level_)
    for char in str_:
        if char != ' ':
            npg.set_char_rgb(npg.charset[char], rgb)
            npg.write()
            await asyncio.sleep_ms(pause_ms)
            npg.set_char_rgb(npg.charset[char], (0, 0, 0))
            npg.write()
        else:
            await asyncio.sleep_ms(pause_ms)
