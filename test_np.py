# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from np_strip_helper import mono_chase, np_arc_weld
from railway import FourAspect


# helper functions

def time_set_strip(nps_, rgb_):
    """ test and time fill-strip method """
    c_time = time.ticks_us()
    nps_.set_strip(rgb_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


async def main():
    """ coro: test NeoPixel strip helper functions """

    pin_number = 27
    n_pixels = 64
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()

    mono_set = [cs.get_rgb('orange', 40),
                cs.get_rgb('orange', 100),
                cs.get_rgb('orange', 150)
                ]

    time_set_strip(nps, mono_set[1])
    await asyncio.sleep_ms(2000)
    nps.clear()
    await asyncio.sleep_ms(20)

    play_ev = asyncio.Event()
    play_ev.set()

    task_0 = asyncio.create_task(np_arc_weld(nps, cs, 0, play_ev))
    task_1 = asyncio.create_task(mono_chase(nps, mono_set, play_ev))
    
    await asyncio.sleep_ms(30_000)
    play_ev.clear()
    print('Give tasks some time to end')
    await asyncio.sleep_ms(5_000)
    nps.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
