# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from np_strip import PixelStrip
from colour_space import ColourSpace
from railway import FourAspect


# helper functions

def time_set_strip(nps_, rgb_):
    """ test and time fill-strip method """
    c_time = time.ticks_us()
    nps_.set_strip_rgb(rgb_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


async def main():
    """ coro: test NeoPixel strip helper functions """

    pin_number = 27
    n_pixels = 64
    nps = PixelStrip(pin_number, n_pixels)
    cs = ColourSpace()

    level = 64
    
    mono_set = [cs.get_rgb('orange', 40), cs.get_rgb('orange', 90), cs.get_rgb('orange', 192)]

    time_set_strip(nps, mono_set[1])
    await asyncio.sleep_ms(2000)

    await nps.mono_chase(mono_set, 20)
    
    nps.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
