# test_np_grid.py

""" test WS1802-related classes
    - test for 8x8 pixel grid
"""

import asyncio
import random
from colour_space import ColourSpace
from pixel_strip import BlockGrid


async def main():
    """ coro: test WS1802 grid methods """

    pin_number = 15
    cs = ColourSpace()
    pg = BlockGrid(
        pin_number, n_cols_=8, n_rows_=8, charset_file='5x7.json')
    off = (0, 0, 0)
    level = 64

    colour_list = ['amber', 'aqua', 'blue', 'cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow']
    cl_len = len(colour_list)

    rgb = cs.get_rgb_lg('dark_orange', level)

    # fill_ functions have implicit write; set_ functions do not
    # fill grid with single grb_
    await pg.fill_grid(rgb, level)
    await asyncio.sleep_ms(1000)
    pg.clear_strip()
    await asyncio.sleep_ms(500)
    
    pix_pause_ms = 20

    print('fill pixels as strip')
    await pg.traverse_strip(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.traverse_strip(off, pix_pause_ms)
    await asyncio.sleep_ms(500)

    print('fill pixels in col, row order')
    await pg.traverse_grid(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.traverse_grid(off, pix_pause_ms)
    await asyncio.sleep_ms(500)
 
    # build list of rgb values at same level
    colour_set = ('red', 'orange', 'yellow', 'green', 'blue', 'purple')
    rgb_set = [cs.get_rgb_lg(c, level) for c in colour_set]

    print('fill cols in sequence')
    await pg.fill_cols(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.fill_cols((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill rows in sequence')
    await pg.fill_rows(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await pg.fill_rows((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    colour = colour_list[random.randrange(cl_len)]
    print(colour)
    rgb = cs.get_rgb_lg(colour, level)

    print('fill diagonals')
    pause_ms = 1000
    for _ in range(12):
        pg.set_diagonal(rgb, mirror=False)
        pg.chipset.write()
        await asyncio.sleep_ms(pause_ms)
        pg.set_diagonal(off, mirror=False)
        pg.chipset.write()
        pg.set_diagonal(rgb, mirror=True)
        pg.chipset.write()
        await asyncio.sleep_ms(pause_ms)
        pg.set_diagonal(off, mirror=True)
        pg.chipset.write()
        pause_ms //= 2
    pg.clear_strip()
    await asyncio.sleep_ms(1000)

    print('display strings')
    await pg.display_string('MERG', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(1000)

    await pg.display_string('3210', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(200)

    await pg.display_string_shift(' Famous Trains Derby ', rgb)
    await asyncio.sleep_ms(1000)
    pg.clear_strip()
    pg.chipset.write()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
