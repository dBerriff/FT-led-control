# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from np_strip_helper import two_flash


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

    pin_number = 11
    n_pixels = 2
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()
    off = (0, 0, 0)

    test_rgb = cs.get_rgb('orange', 100)
    
    time_set_strip(nps, test_rgb)
    nps.set_strip(off)
    nps.write()
    await asyncio.sleep_ms(20)
    

    nps.set_pixel(0, cs.get_rgb('green', 100))
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.set_pixel(0, off)
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_pixel(1, cs.get_rgb('blue', 100))
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.set_pixel(1, off)
    nps.write()
    await asyncio.sleep_ms(20)

    nps.set_strip(test_rgb)
    nps.write()
    await asyncio.sleep_ms(1_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(20)

    # test twin pixel flash: red
    test_rgb = cs.get_rgb('red', 100)
    # asyncio Event controls flashing
    do_flash = asyncio.Event()
    # create the task, adding to scheduler
    asyncio.create_task(two_flash(nps, 0, test_rgb, do_flash))
    print('Wait for it...')
    await asyncio.sleep_ms(1_000)
    print('Now!')
    # set the flag
    do_flash.set()
    await asyncio.sleep_ms(10_000)
    do_flash.clear()
    print('Wait for more...')
    await asyncio.sleep_ms(5_000)
    print('Now!')
    # set the flag
    do_flash.set()
    await asyncio.sleep_ms(10_000)
    do_flash.clear()
    await asyncio.sleep_ms(200)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
