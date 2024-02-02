# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid
from char_set import charset_1_8x8 as charset
import led


# helper functions

def blank_grid(grid_):
    """ fill grid with (0, 0, 0) and pause """
    grid_.fill_grid((0, 0, 0))
    grid_.write()


async def cycle_colours(strip, rgb_set, pause=100):
    """ step through grid as a strip, cycling colour """
    cs_mod = len(rgb_set)
    for index in range(strip.n_pixels):
        rgb = rgb_set[index % cs_mod]
        strip[index] = rgb
        strip.write()
        await asyncio.sleep_ms(pause)
        # strip[index] = strip.OFF
        

async def cycle_cr_colours(grid, rgb_set, pause=20):
    """ step through grid in col, row order; cycling colour """
    clrs_mod = len(rgb_set)
    c_r_index = grid.Coord(0, 0)
    for index in range(grid.n_pixels):
        rgb = rgb_set[index % clrs_mod]
        grid[grid.coord_index[c_r_index]] = rgb
        grid.write()
        await asyncio.sleep_ms(pause)
        c_r_index = grid.coord_inc(c_r_index)


async def main():
    """ set NeoPixel values on grid """

    async def display_string(npg_, str_, rgb_, pause_=500):
        """ cycle through the letters in a string """
        for char_ in str_:
            npg_.display_char(char_, rgb_)
            await asyncio.sleep_ms(pause_)

    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    print(npg, npg.n)
    colours = npg.colours
    level = 63  # range 0 to 255
    gamma = 2.6
    rgb_gamma = led.get_rgb_gamma(gamma)  # conversion tuple
    rgb = led.get_rgb_l_g_c(colours['orange'], level, rgb_gamma)
    off = (0, 0, 0)
    npg.charset = charset  # load charset into object
    
    # fill grid with single colour
    npg.fill_grid(rgb)
    npg.write()
    await asyncio.sleep_ms(500)
    blank_grid(npg)
    await asyncio.sleep_ms(200)

    # list of rgb colours for demo
    cycle_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = tuple([led.get_rgb_l_g_c(
        npg.colours[c], level, rgb_gamma) for c in cycle_set])
    rgb_n = len(rgb_set)

    # cycle through grid as a strip
    await cycle_colours(npg, rgb_set, 20)
    await asyncio.sleep_ms(2000)
    blank_grid(npg)
    
    # cycle through grid in column, row order
    await cycle_cr_colours(npg, rgb_set)
    await asyncio.sleep_ms(1000)
    await cycle_cr_colours(npg, [off])
    blank_grid(npg)
    await asyncio.sleep_ms(2000)
    
    # fill columns in sequence
    for c in range(npg.n_cols):
        npg.fill_col(c, rgb_set[c % rgb_n])
        npg.write()
        await asyncio.sleep_ms(200)
    await asyncio.sleep_ms(2000)
    blank_grid(npg)
 
    # fill rows in sequence
    for r in range(npg.n_rows):
        npg.fill_row(r, rgb_set[r % rgb_n])
        npg.write()
        await asyncio.sleep_ms(200)
    await asyncio.sleep_ms(2000)
    blank_grid(npg)


    pause = 2000
    # demo fill_diagonal
    rgb = led.get_rgb_l_g_c(colours['aqua'], level, rgb_gamma)
    for _ in range(8):
        npg.fill_diagonal(rgb)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off)
        npg.write()
        npg.fill_diagonal(rgb, reverse=True)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off, reverse=True)
        npg.write()
        pause = pause // 2
    blank_grid(npg)
    await asyncio.sleep_ms(2000)

    rgb = led.get_rgb_l_g_c(colours['blue'], level, rgb_gamma)
    await display_string(npg, 'MERG PI SIG', rgb)
    blank_grid(npg)
    await asyncio.sleep_ms(1000)
    await display_string(npg, 'FAMOUS TRAINS DERBY', rgb)
    blank_grid(npg)
    await asyncio.sleep_ms(1000)
    await display_string(npg, '0123456789', rgb)
    blank_grid(npg)
    await asyncio.sleep_ms(1000)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
