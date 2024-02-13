# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
import random
from neo_pixel import PixelStrip
from neo_pixel_helper import np_arc_weld, np_twinkler, \
     mono_chase, colour_chase
from colour_space import ColourSpace


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
    n_pixels = 30
    nps = PixelStrip(pin_number, n_pixels)
    cs = ColourSpace()

    colour_list = ['amber', 'aqua', 'blue','cyan', 'ghost_white', 'gold',
                   'green', 'jade', 'magenta', 'mint_cream', 'old_lace',
                   'orange', 'dark_orange', 'pink', 'purple', 'red', 'snow',
                   'teal', 'white', 'yellow'
                   ]

    cl_len = len(colour_list)

    level = 128

    mono_set = [cs.get_rgb('orange', 40), cs.get_rgb('orange', 90), cs.get_rgb('orange', 180)]
    nps[1] = mono_set[2]
    nps[0] = nps[1]
    nps.write()
    await asyncio.sleep_ms(1000)
    await mono_chase(nps, mono_set, 20)
    
    nps.clear()
    await asyncio.sleep_ms(20)
    
    colour_set = [cs.get_rgb('purple', 128),
                  cs.get_rgb('blue', 128),
                  cs.get_rgb('green', 128),
                  cs.get_rgb('yellow', 128),
                  cs.get_rgb('red', 128)
                  ]
    await colour_chase(nps, colour_set, 200)
    
    nps.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
