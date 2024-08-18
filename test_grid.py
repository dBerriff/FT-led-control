# test_grid.py

""" test WS1802-related classes
    - test for 8x8 pixel grid
"""

import machine
import asyncio
import random
from colour_space import ColourSpace
from plasma import Plasma2350
from ws2812 import Ws2812
from pixel_strip import Grid
import time


async def main():
    from adc import Adc

    async def monitor_current(adc_):
        """ monitor Plasma 2350 current """
        while True:
            print(f'{adc_.get_u16():,}')
            await asyncio.sleep_ms(200)

    """ coro: test WS1802 grid methods """

    print(f'Processor f: {machine.freq():,}')
    grid_cols = 8
    grid_rows = 8
    # set board and strip chipset methods
    cs = ColourSpace()
    board = Plasma2350()
    board.set_onboard((0, 64, 0))
    driver = Ws2812(board.DATA)
    pg = Grid(driver, grid_cols, grid_rows, '5x7.json')

    adc_current = Adc('adc3')
    asyncio.create_task(monitor_current(adc_current))

    off = (0, 0, 0)
    level = 64

    colour_list = ['amber', 'aqua', 'blue', 'cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow']
    cl_len = len(colour_list)

    pix_pause_ms = 20
    colour = colour_list[random.randrange(cl_len)]
    print(colour)
    rgb = cs.rgb_lg(colour, level)

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
    await pg.display_string_rgb('Pimoroni', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(1000)

    await pg.display_string_rgb('Plasma 2350', rgb)
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
