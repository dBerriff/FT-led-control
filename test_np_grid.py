# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid
from colour import colours, Colour
from char_set import charset_1_8x8 as charset


# helper functions

async def traverse_strip(grid, rgb, pause_ms=20):
    """ step through grid as a strip; cycling colour """
    for index in range(grid.n_pixels):
        grid[index] = rgb
        grid.write()
        await asyncio.sleep_ms(pause_ms)


async def traverse_grid(grid, rgb, pause_ms=20):
    """ fill each pixel in grid cooord order """
    for row in range(grid.n_rows):
        for col in range(grid.n_cols):
            grid[grid.coord_index[(col, row)]] = rgb
            grid.write()
            await asyncio.sleep_ms(pause_ms)


async def fill_cols(grid, rgb_set, pause_ms=20):
    """ step through cols """
    n_colours = len(rgb_set)
    for c in range(grid.n_cols):
        grid.fill_col(c, rgb_set[c % n_colours])
        grid.write()
        await asyncio.sleep_ms(pause_ms)


async def fill_rows(grid, rgb_set, pause_ms=20):
    """ step through rows """
    n_colours = len(rgb_set)
    for r in range(grid.n_rows):
        grid.fill_row(r, rgb_set[r % n_colours])
        grid.write()
        await asyncio.sleep_ms(pause_ms)


async def display_string(npg_, str_, rgb_, pause_ms=500):
    """ cycle through the letters in a string """
    for char_ in str_:
        npg_.display_char(char_, rgb_)
        npg_.write()
        await asyncio.sleep_ms(pause_ms)


async def main():
    """ set NeoPixel values on grid """

    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    npg.charset = charset  # load charset into object
    off = (0, 0, 0)

    colour = Colour(colours['dark_orange'])
    rgb = colour.get_rgb(68)

    # fill grid with single colour
    npg.fill_grid(rgb)
    npg.write()
    await asyncio.sleep_ms(500)
    npg.clear()
    await asyncio.sleep_ms(500)

    print('fill pixels as strip')
    await traverse_strip(npg, rgb, 20)
    await asyncio.sleep_ms(1000)
    await traverse_strip(npg, off, 20) 
    await asyncio.sleep_ms(1000)

    print('fill pixels in col, row order')
    await traverse_grid(npg, rgb, 20)
    await asyncio.sleep_ms(1000)
    await traverse_grid(npg, off, 20) 
    await asyncio.sleep_ms(1000)
     
    # build list of rgb values
    colour_tuple = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = [Colour(colours[c]).get_rgb(63) for c in colour_tuple]

    print('fill cols in sequence')
    await fill_cols(npg, rgb_set)
    await asyncio.sleep_ms(1000)
    await fill_cols(npg, (off,))
    await asyncio.sleep_ms(1000)

    print('fill rows in sequence')
    await fill_rows(npg, rgb_set)
    await asyncio.sleep_ms(1000)
    await fill_rows(npg, (off,))
    await asyncio.sleep_ms(1000)

    print('fill diagonals')
    colour = Colour(colours['aqua'])
    rgb = colour.get_rgb(68)
    pause = 1000
    for _ in range(12):
        npg.fill_diagonal(rgb)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off)
        npg.write()
        npg.fill_diagonal(rgb, mirror=True)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off, mirror=True)
        npg.write()
        pause = pause // 2
    npg.clear()
    await asyncio.sleep_ms(2000)

    colour = Colour(colours['blue'])
    rgb = colour.get_rgb(68)
    await display_string(npg, 'MERG PI SIG', rgb)
    npg.clear()
    await asyncio.sleep_ms(1000)
    await display_string(npg, 'FAMOUS TRAINS DERBY', rgb)
    npg.clear()
    await asyncio.sleep_ms(1000)
    await display_string(npg, '0123456789', rgb)
    npg.clear()
    await asyncio.sleep_ms(1000)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
