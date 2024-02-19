# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from np_strip import PixelStrip
from colour_space import ColourSpace
from railway import FourAspect


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

    level = 64

    mono_set = [cs.get_rgb('orange', 40), cs.get_rgb('orange', 90), cs.get_rgb('orange', 192)]
    await nps.mono_chase(mono_set, 20)
    
    nps.clear()
    await asyncio.sleep_ms(20)
    """    
    colour_set = [cs.get_rgb('purple', 64),
                  cs.get_rgb('blue', 64),
                  cs.get_rgb('green', 64),
                  cs.get_rgb('yellow', 64),
                  cs.get_rgb('red', 64)
                  ]
    await nps.colour_chase(colour_set, 200)
    """    
    t_4 = FourAspect(nps, cs, 0, level)
    print(t_4, t_4.aspect_codes)
    sequence = ['red', 'yellow', 'double yellow', 'green']
    for aspect in sequence:
        print(aspect)
        t_4.set_aspect(aspect)
        await asyncio.sleep_ms(2_000)
    await asyncio.sleep_ms(2_000)

    for n in [0, 1, 2, 3, 3, 2, 1, 0]:
        print('clear blocks:', n)
        t_4.set_by_blocks_clear(n)
        await asyncio.sleep_ms(2_000)

    nps.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
