# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from neo_pixel import PixelStrip
from colour_space import ColourSpace
from neo_pixel_helper import np_arc_weld, np_twinkler


# helper functions

async def time_set_strip(nps_, rgb_, level_):
    """ coro: test and time fill-strip method """
    c_time = time.ticks_us()
    nps_.set_strip(rgb_, level_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


async def main():
    """ coro: test NeoPixel strip helper functions """

    pin_number = 27
    n_pixels = 64
    nps = PixelStrip(pin_number, n_pixels)

    rgb_list = ['red', (0, 255, 0), 'blue']
    
    for level in range(32, 192, 32):
        print('set_pixel', level)
        for rgb in rgb_list:
            nps.set_pixel(5, rgb, level)
            nps.write()
            await asyncio.sleep_ms(1000)
            nps.clear()

    level = 64
    
    print('set_strip')
    for rgb in rgb_list:
        nps.set_strip(rgb, level)
        nps.write()
        await asyncio.sleep_ms(1000)
        nps.clear()

    print('set_range')
    for rgb in rgb_list:
        nps.set_range(32, 16, rgb, level)
        nps.write()
        await asyncio.sleep_ms(1000)
        nps.clear()
    
    print('set_range_c_list')
    c_list = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    nps.set_range_c_list(32, 16, c_list, level)
    nps.write()
    await asyncio.sleep_ms(1000)

    rgb = 'ghost_white'
    
    print('time set_strip')
    await time_set_strip(nps, rgb, level)
    await asyncio.sleep_ms(1000)    

    nps.clear()
    await asyncio.sleep_ms(20)
    
    print('arc-weld effect')
    await np_arc_weld(nps, 0)
    
    print('gas-lamp twinkle')
    await np_twinkler(nps, 2)

    nps.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
