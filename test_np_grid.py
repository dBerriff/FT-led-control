# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
import gc
import random
from colour_space import ColourSpace
from np_grid import PixelGrid


async def main():
    """ coro: test NeoPixel grid helper functions """

    pin_number = 27
    cs = ColourSpace()
    npg = PixelGrid(
        pin_number, n_cols_=8, n_rows_=8, charset_file='5x7.json')
    off = (0, 0, 0)
    level = 64
    gc.collect()

    colour_list = ['amber', 'aqua', 'blue', 'cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow']
    cl_len = len(colour_list)

    rgb = 'dark_orange'
    # fill grid with single colour
    await npg.fill_grid(rgb, level)
    await asyncio.sleep_ms(1000)
    npg.clear()
    await asyncio.sleep_ms(1000)

    print('fill pixels as strip')
    await npg.traverse_strip(rgb, level)
    await asyncio.sleep_ms(1000)
    await npg.traverse_strip(off, level) 
    await asyncio.sleep_ms(500)

    print('fill pixels in col, row order')
    await npg.traverse_grid(rgb, level)
    await asyncio.sleep_ms(1000)
    await npg.traverse_grid(off, level) 
    await asyncio.sleep_ms(500)
 
    # build list of rgb values at same level
    rgb_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'

    print('fill cols in sequence')
    await npg.fill_cols(rgb_set, level)
    await asyncio.sleep_ms(1000)
    await npg.fill_cols((off,), level)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill rows in sequence')
    await npg.fill_rows(rgb_set, level)
    await asyncio.sleep_ms(1000)
    await npg.fill_rows((off,), level)  # list/tuple required
    await asyncio.sleep_ms(500)

    clr = colour_list[random.randrange(cl_len)]
    print(clr)
    
    print('fill diagonals')
    pause_ms = 1000
    for _ in range(12):
        npg.set_diagonal(clr, level)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.set_diagonal(off, level)
        npg.write()
        npg.set_diagonal(clr, level, mirror=True)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.set_diagonal(off, level, mirror=True)
        npg.write()
        pause_ms //= 2
    npg.clear()
    await asyncio.sleep_ms(2000)

    rgb = cs.get_rgb(clr, level)

    print('display strings')
    await npg.display_string_rgb('MERG', rgb)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(1000)

    await npg.display_string_rgb('0123456789', rgb)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
