# test_grid.py

""" test WS1802-related classes
    - test for 8x8 pixel grid
"""

import machine
import asyncio
import random
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812
from pixel_strip import PixelStrip, Grid
import time

def time_set_strip(nps_, rgb_):
    """ test and time fill-strip method """
    rgb = rgb_
    t_0 = time.ticks_us()
    nps_.set_strip_rgb(rgb)
    t_1 = time.ticks_us()
    print(f'Time to fill array: {time.ticks_diff(t_1, t_0):,}us')
    t_0 = time.ticks_us()
    nps_.write()
    t_1 = time.ticks_us()
    print(f'Time to write to WS2812: {time.ticks_diff(t_1, t_0):,}us')

async def main():
    """ coro: test WS1802 grid methods """
    print(f'Processor f: {machine.freq():,}')
    grid_cols = 8
    grid_rows = 8
    # set board and strip chipset methods
    cs = ColourSpace()
    board = Plasma2040()
    board.set_onboard((0, 64, 0))
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, grid_rows * grid_cols)
    pg = Grid(driver, grid_cols, grid_rows, '5x7.json')
    off = (0, 0, 0)
    level = 64

    colour_list = ['amber', 'aqua', 'blue', 'cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow']
    cl_len = len(colour_list)

    pix_pause_ms = 0
    colour = colour_list[random.randrange(cl_len)]
    print(colour)
    rgb = cs.rgb_lg(colour, level)

    time_set_strip(nps, rgb)
    time.sleep_ms(1000)
    nps.clear_strip()
    time.sleep_ms(500)

    print('fill pixels as strip')
    await pg.traverse_strip_rgb(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.traverse_strip_rgb(off, pix_pause_ms)
    await asyncio.sleep_ms(500)

    print('fill pixels in cols, rows order')
    await pg.traverse_grid_rgb(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.traverse_grid_rgb(off, pix_pause_ms)
    await asyncio.sleep_ms(500)
 
    # build list of rgb values at same level
    colour_set = ('red', 'orange', 'yellow', 'green', 'blue', 'purple')
    rgb_set = [cs.rgb_lg(c, level) for c in colour_set]

    print('fill cols in sequence')
    await pg.fill_cols_rgbset(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.fill_cols_rgbset((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill rows in sequence')
    await pg.fill_rows_rgbset(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.fill_rows_rgbset((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    colour = colour_list[random.randrange(cl_len)]
    print(colour)
    rgb = cs.rgb_lg(colour, level)

    print('fill diagonals')
    pause_ms = 1000
    for _ in range(12):
        pg.set_diagonal_rgb(rgb, mirror=False)
        pg.write()
        await asyncio.sleep_ms(pause_ms)
        pg.set_diagonal_rgb(off, mirror=False)
        pg.write()
        pg.set_diagonal_rgb(rgb, mirror=True)
        pg.write()
        await asyncio.sleep_ms(pause_ms)
        pg.set_diagonal_rgb(off, mirror=True)
        pg.write()
        pause_ms //= 2
    pg.clear_strip()
    await asyncio.sleep_ms(1000)

    print('display strings')
    await pg.display_string_rgb('MERG', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(1000)

    await pg.display_string_rgb('3210', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(1000)
    board.set_onboard((0, 0, 0))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
