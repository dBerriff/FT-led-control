# test_np_grid.py

""" test WS1802-related classes
    - test for 8x8 pixel grid
"""

import asyncio
import gc
import random
from colour_space import ColourSpace
from np_grid import Ws2812Grid


async def main():
    """ coro: test WS1802 grid methods """

    pin_number = 27
    cs = ColourSpace()
    npg = Ws2812Grid(
        pin_number, n_cols_=8, n_rows_=8, charset_file='5x7.json')
    off = (0, 0, 0)
    level = 64
    gc.collect()

    colour_list = ['amber', 'aqua', 'blue', 'cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow']
    cl_len = len(colour_list)

    rgb = cs.get_rgb('dark_orange', level)
    # fill grid with single colour
    await npg.fill_grid(rgb, level)
    await asyncio.sleep_ms(1000)
    npg.clear()
    await asyncio.sleep_ms(500)
    
    pix_pause_ms = 20

    print('fill pixels as strip')
    await npg.traverse_strip(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await npg.traverse_strip(off, pix_pause_ms) 
    await asyncio.sleep_ms(500)

    print('fill pixels in col, row order')
    await npg.traverse_grid(rgb, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await npg.traverse_grid(off, pix_pause_ms) 
    await asyncio.sleep_ms(500)
 
    # build list of rgb values at same level
    colour_set = ('red', 'orange', 'yellow', 'green', 'blue', 'purple')
    rgb_set = [cs.get_rgb(c, level) for c in colour_set]

    print('fill cols in sequence')
    await npg.fill_cols(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await npg.fill_cols((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill rows in sequence')
    await npg.fill_rows(rgb_set, pix_pause_ms)
    await asyncio.sleep_ms(1000)
    await npg.fill_rows((off,), pix_pause_ms)  # list/tuple required
    await asyncio.sleep_ms(500)

    colour = colour_list[random.randrange(cl_len)]
    print(colour)
    rgb = cs.get_rgb(colour, level)

    print('fill diagonals')
    pause_ms = 1000
    for _ in range(12):
        npg.set_diagonal(rgb, mirror=False)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.set_diagonal(off, mirror=False)
        npg.write()
        npg.set_diagonal(rgb, mirror=True)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.set_diagonal(off, mirror=True)
        npg.write()
        pause_ms //= 2
    npg.clear()
    await asyncio.sleep_ms(2000)

    print('display strings')
    await npg.display_string('MERG', rgb)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(1000)

    await npg.display_string('0123456789', rgb)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(200)

    await npg.display_string_shift(' This is a test.', rgb, 1000)
    await asyncio.sleep_ms(1000)
    npg.clear()
    npg.write()
    await asyncio.sleep_ms(20)



if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
