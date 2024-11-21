# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from colour_space import ColourSpace
from plasma import Plasma2040 as DriverBoard
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

    board = DriverBoard()  # board parameters
    print(board.NAME)
    board.set_onboard((0, 32, 0))  # RGB LED
    driver = Ws2812(board.strip_pins['dat'])  # for pixel-strip logic
    nps = PixelStrip(driver, n_pixels)  #
    print(f'Driver pin: {nps.driver.pin}')

    time_set_strip(nps, test_rgb)
    time.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(500)

    nps.set_pixel_rgb(0, test_rgb)
    nps.write()
    await asyncio.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(500)

    nps.set_strip_rgb(test_rgb)
    nps.write()
    await asyncio.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(500)

    nps.set_range_rgb(16, 8, test_rgb)
    nps.write()
    await asyncio.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(500)

    nps.set_strip_rgb(test_rgb)
    nps.write()
    await asyncio.sleep_ms(20)
    for offset in range(1, n_pixels+1):
        off_list = range(0, offset)
        # print(off_list)
        on_list = range(offset, n_pixels)
        nps.set_list_rgb(off_list, (0, 0, 0))
        nps.set_list_rgb(on_list, test_rgb)
        nps.write()
        await asyncio.sleep_ms(20)
    board.set_onboard((0, 0, 0))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
