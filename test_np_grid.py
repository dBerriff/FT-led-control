# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid
from char_set import charset_2_8x8 as charset
# from neopixel import NeoPixel


# helper functions

def blank_strip(strip):
    """ fill grid with (0, 0, 0) and pause """
    strip.fill_strip(strip.OFF)
    strip.write()


async def cycle_colours(strip, rgb_set, pause=100):
    """ step through strip, cycling colour """
    cs_mod = len(rgb_set)
    for index in range(strip.n_pixels):
        rgb = rgb_set[index % cs_mod]
        strip[index] = rgb
        strip.write()
        await asyncio.sleep_ms(pause)
        # strip[index] = strip.OFF
        

async def cycle_grid_colours(grid, rgb_set, pause=20):
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

    async def display_string(npg_, str_, rgb_, pause=500):
        """ cycle through the letters in a string """
        for char_ in str_:
            npg_.display_char(char_, rgb_)
            await asyncio.sleep_ms(pause)

    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    print(npg, npg.n)
    colours = npg.Colours
    level = 63  # range 0 to 255
    rgb = npg.get_rgb_l_g_c(colours['orange'], level)
    off = npg.OFF
    npg.charset = charset  # for later module attribute
    
    npg.fill_grid(rgb)
    npg.write()
    await asyncio.sleep_ms(500)
    blank_strip(npg)
    await asyncio.sleep_ms(200)
    
    cycle_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = [npg.get_rgb_l_g_c(npg.Colours[c], level) for c in cycle_set]

    await cycle_colours(npg, rgb_set, 20)
    await asyncio.sleep_ms(1000)
    blank_strip(npg)
    
    await cycle_grid_colours(npg, rgb_set)
    await asyncio.sleep_ms(1000)
    await cycle_grid_colours(npg, [off])
    blank_strip(npg)
    await asyncio.sleep_ms(1000)

    pause = 2000
    # demo fill_diagonal
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
    blank_strip(npg)
    await asyncio.sleep_ms(1000)

    rgb = npg.get_rgb_l_g_c(colours['blue'], level)
    await display_string(npg, 'MERG PI SIG', rgb)
    await asyncio.sleep_ms(1000)
    await display_string(npg, 'FAMOUS TRAINS DERBY ', rgb)
    await asyncio.sleep_ms(1000)
    await display_string(npg, '0123456789 ', rgb)
    await asyncio.sleep_ms(1000)

    blank_strip(npg)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
