# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelGrid
import gc
from np_grid_helper import fill_grid, traverse_strip, \
     traverse_grid, fill_cols, fill_rows, display_string


async def main():
    """ coro: test NeoPixel grid helper functions """

    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    off = (0, 0, 0)
    level = 64
    gc.collect()
    rgb = 'dark_orange'
    
    # fill grid with single colour
    await fill_grid(npg, rgb, level)
    await asyncio.sleep_ms(500)
    npg.clear()
    npg.write()
    await asyncio.sleep_ms(500)

    print('fill pixels as strip')
    await traverse_strip(npg, rgb, level)
    await asyncio.sleep_ms(500)
    await traverse_strip(npg, off, level) 
    await asyncio.sleep_ms(500)

    print('fill pixels in col, row order')
    await traverse_grid(npg, rgb, level)
    await asyncio.sleep_ms(500)
    await traverse_grid(npg, off, level) 
    await asyncio.sleep_ms(500)
     
    # build list of rgb values at same level
    rgb_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'

    print('fill cols in sequence')
    await fill_cols(npg, rgb_set, level)
    await asyncio.sleep_ms(500)
    await fill_cols(npg, (off,), level)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill rows in sequence')
    await fill_rows(npg, rgb_set, level)
    await asyncio.sleep_ms(500)
    await fill_rows(npg, (off,), level)  # list/tuple required
    await asyncio.sleep_ms(500)

    print('fill diagonals')
    rgb = 'aqua'
    pause_ms = 1000
    for _ in range(12):
        npg.fill_diagonal(rgb, level)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.fill_diagonal(off, level)
        npg.write()
        npg.fill_diagonal(rgb, level, mirror=True)
        npg.write()
        await asyncio.sleep_ms(pause_ms)
        npg.fill_diagonal(off, level, mirror=True)
        npg.write()
        pause_ms //= 2
    npg.clear()
    await asyncio.sleep_ms(2000)

    await display_string(npg, 'MERG PI SIG', rgb, level)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(1000)
    await display_string(npg, 'Famous Trains Derby', rgb, level)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(1000)
    await display_string(npg, '0123456789', rgb, level)
    npg.clear()
    gc.collect()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
