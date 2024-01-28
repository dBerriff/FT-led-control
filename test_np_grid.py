# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid
from char_set import charset_2_8x8 as charset


def blank_strip(strip):
    """ fill grid with (0, 0, 0) and pause """
    strip.fill_strip(strip.OFF)
    strip.write()


async def cycle_colours(strip, colour_set, level, pause=200):
    """ step through strip, cycling colour """
    cs_mod = len(colour_set)
    for index in range(strip.n_pixels):
        rgb = strip.Colours[colour_set[index % cs_mod]]
        rgb = strip.get_rgb_l_g_c(rgb, level)
        strip[index] = rgb
        strip.write()
        await asyncio.sleep_ms(pause)
        # strip[index] = strip.OFF
        

async def cycle_grid_colours(grid, colour_set, level, pause=200):
    """ step through grid in col, row order; cycling colour """
    cs_mod = len(colour_set)
    cr = grid.Coord(0, 0)
    for index in range(grid.n_pixels):
        rgb = grid.Colours[colour_set[index % cs_mod]]
        rgb = grid.get_rgb_l_g_c(rgb, level)
        grid_index = grid.coord_index[cr]
        grid[grid_index] = rgb
        grid.write()
        await asyncio.sleep_ms(pause)
        # grid[grid_index] = grid.OFF
        cr = grid.coord_inc(cr)


async def main():
    """ set NeoPixel values on grid """
    
    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    colours = npg.Colours
    # following list actions raise errors if combined
    colour_list = list(colours.keys())
    colour_list.sort()
    colour_list = tuple(colour_list)
    print(f'colour list: {colour_list}')
    # level: intensity in range 0 to 255
    level = 63
    rgb = npg.get_rgb_l_g_c(colours['orange'], level)
    off = npg.OFF
    npg.charset = charset  # for later module attribute
    
    npg.fill_grid(rgb)
    npg.write()
    await asyncio.sleep_ms(200)
    blank_strip(npg)
    await asyncio.sleep_ms(200)
    
    clr_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    await cycle_colours(npg, clr_set, level, 20)
    await asyncio.sleep_ms(5000)
    blank_strip(npg)
    await cycle_grid_colours(npg, clr_set, level)
    await asyncio.sleep_ms(5000)
    blank_strip(npg)

    pause = 2000
    for _ in range(8):
        npg.fill_diagonal(rgb)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off)
        npg.write()
        npg.fill_diagonal(rgb, True)
        npg.write()
        await asyncio.sleep_ms(pause)
        npg.fill_diagonal(off, True)
        npg.write()
        pause = pause // 2
    blank_strip(npg)

    rgb = npg.get_rgb_l_g_c(colours['blue'], level)
    await npg.display_string('MERG ', rgb)
    await asyncio.sleep_ms(1000)
    await npg.display_string('FAMOUS TRAINS DERBY ', rgb)
    await asyncio.sleep_ms(1000)

    blank_strip(npg)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
