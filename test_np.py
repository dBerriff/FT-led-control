# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from np_strip_helper import mono_chase, colour_chase, two_flash


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

    pin_number = 15
    n_pixels = 30
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()

    test_rgb = cs.get_rgb('orange', 100)
    list_rgb = [cs.get_rgb('blue', 192), cs.get_rgb('red', 96), cs.get_rgb('green', 32)]
    level = 128
    time_set_strip(nps, test_rgb)
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    nps.set_pixel(0, test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    nps.set_strip(test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    nps.set_range(8, 8, test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    nps.set_list((0, 2, 4, 6), test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    ev = asyncio.Event()
    ev.set()
    asyncio.create_task(mono_chase(nps, list_rgb, ev, 20))
    await asyncio.sleep_ms(10_000)
    print('Clear ev')
    ev.clear()
    await asyncio.sleep_ms(20)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(5_000)

    # test twin pixel flash: red
    test_rgb = cs.get_rgb('red', level)
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
