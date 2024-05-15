# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from colour_space import ColourSpace
# from plasma_2040 import Plasma2040
from dh_2040 import Dh2040
from ws2812 import Ws2812
from pixel_strip import PixelStrip


# helper functions

def time_set_strip(nps_, rgb_):
    """ test and time fill-strip method """
    rgb = rgb_
    t_0 = time.ticks_us()
    nps_.set_strip_rgb(rgb)
    t_1 = time.ticks_us()
    print(f'Time to fill: {time.ticks_diff(t_1, t_0):,}us')
    t_0 = time.ticks_us()
    nps_.write()
    t_1 = time.ticks_us()
    print(f'Time to write: {time.ticks_diff(t_1, t_0):,}us')


async def main():
    """ coro: test NeoPixel strip helper functions """

    n_pixels = 30
    # set board and strip chipset methods
    cs = ColourSpace()
    test_rgb = cs.rgb_lg('orange', 100)
    list_rgb = [cs.rgb_lg('blue', 192),
                cs.rgb_lg('red', 96),
                cs.rgb_lg('green', 32)]

    board = Dh2040()
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, n_pixels)
    print(nps.driver.pin)

    time_set_strip(nps, test_rgb)
    time.sleep_ms(1000)
    nps.clear_strip()
    time.sleep_ms(500)

    nps.set_pixel_rgb(0, test_rgb)
    nps.write()
    time.sleep_ms(1000)
    nps.clear_strip()
    time.sleep_ms(500)

    nps.set_strip_rgb(test_rgb)
    nps.write()
    time.sleep_ms(1000)
    nps.clear_strip()
    time.sleep_ms(500)

    nps.set_range_rgb(16, 8, test_rgb)
    nps.write()
    time.sleep_ms(1000)
    nps.clear_strip()
    time.sleep_ms(500)

    i_list = range(0, 30, 3)
    nps.set_list_rgb(i_list, test_rgb)
    nps.write()
    time.sleep_ms(5000)
    nps.clear_strip()
    time.sleep_ms(500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
