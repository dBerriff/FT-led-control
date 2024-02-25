# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace


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

    test_rgb = cs.get_rgb('orange', 100)
    
    time_set_strip(nps, test_rgb)
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_pixel(0, test_rgb)
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_strip(test_rgb)
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_range(8, 8, test_rgb)
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_list((0, 2, 4, 6), test_rgb)
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
