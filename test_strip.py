# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812
from pixel_strip import PixelStrip
from pixel_strip_helper import colour_chase, two_flash


# helper functions

def time_set_strip(nps_, rgb_):
    """ test and time fill-strip method """
    rgb = rgb_
    c_time = time.ticks_us()
    nps_.set_strip_rgb(rgb)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


async def main():
    """ coro: test NeoPixel strip helper functions """

    n_pixels = 30
    # set board and strip chipset methods
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    # ps = PixelStrip(driver, n_pixels)
    cs = ColourSpace()
    nps = PixelStrip(driver, n_pixels)

    test_rgb = cs.rgb_lg('orange', 100)
    list_rgb = [cs.rgb_lg('blue', 192),
                cs.rgb_lg('red', 96),
                cs.rgb_lg('green', 32)]
    level = 128

    print('Time strip fill and write')
    time_set_strip(nps, test_rgb)
    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)

    print('Set single pixel')
    nps.set_pixel_rgb(0, test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)

    print('Set strip')
    nps.set_strip_rgb(test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)

    print('Set range')
    nps.set_range_rgb(8, 8, test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)

    print('Set list')
    nps.set_list_rgb((0, 2, 4, 6), test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)

    print('Set colour chase')
    ev = asyncio.Event()
    ev.set()
    asyncio.create_task(colour_chase(nps, list_rgb, ev, 20))
    await asyncio.sleep_ms(10_000)
    print('Clear colour chase ev')
    ev.clear()
    await asyncio.sleep_ms(20)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(5_000)

    print('Set twin pixel flash: red')
    test_rgb = cs.rgb_lg('red', level)
    # asyncio Event controls flashing
    do_flash = asyncio.Event()
    asyncio.create_task(two_flash(nps, 0, test_rgb, do_flash))
    print('Wait for it...')
    await asyncio.sleep_ms(2_000)
    print('Now!')
    
    # set the flag
    do_flash.set()
    await asyncio.sleep_ms(5_000)
    do_flash.clear()
    print('Wait for more...')
    await asyncio.sleep_ms(3_000)
    print('Now!')
    
    # set the flag
    do_flash.set()
    await asyncio.sleep_ms(5_000)
    do_flash.clear()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
