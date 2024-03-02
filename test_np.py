# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from neo_pixel_helper import mono_chase, colour_chase, set_colour_list


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

    pin_number = 28
    n_pixels = 300
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()

    test_rgb = cs.get_rgb((200, 200, 255), 255)
    list_rgb = [cs.get_rgb('green', 126), cs.get_rgb('red', 126),  cs.get_rgb('blue', 126)]
    list_1 = [cs.get_rgb('green', 126), cs.get_rgb('red', 126), cs.get_rgb('blue', 126)]
    list_2 = [cs.get_rgb('red', 126), cs.get_rgb('blue', 126), cs.get_rgb('green', 126)]
    list_3 = [cs.get_rgb('blue', 126), cs.get_rgb('green', 126), cs.get_rgb('red', 126)]
    
    time_set_strip(nps, test_rgb)
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)
    """
    nps.set_pixel(0, test_rgb)
    nps.write()
    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)
    """
    set_colour_list(nps, list_1)
    nps.write()
    await asyncio.sleep_ms(5000)
    set_colour_list(nps, list_2)
    nps.write()
    await asyncio.sleep_ms(5000)
    set_colour_list(nps, list_3)
    nps.write()
    await asyncio.sleep_ms(5000)
    nps.clear()
    nps.write()

    while True:
        for i in range(25, 179):
            test_rgb = cs.get_rgb((255, 255, 255), i)
            nps.set_range(0, 179, test_rgb)
            nps.write()
            await asyncio.sleep_ms(2)
        for i in range(179, 25, -1):
            test_rgb = cs.get_rgb((200, 200, 255), i)
            nps.set_range(0, 179, test_rgb)
            nps.write()
            await asyncio.sleep_ms(2)
        """
        nps.set_range(100, 100, test_rgb)
        nps.write()
        await asyncio.sleep_ms(5_000)
        nps.clear()
        nps.write()
        await asyncio.sleep_ms(200)

        nps.set_list((0, 100, 102, 104), test_rgb)
        nps.write()
        await asyncio.sleep_ms(5_000)
        nps.clear()
        nps.write()
        await asyncio.sleep_ms(200)

        ev = asyncio.Event()
        ev.set()
        asyncio.create_task(mono_chase(nps, list_rgb, ev, 20))
        await asyncio.sleep_ms(60_000)
        print('Clear ev')
        ev.clear()
        await asyncio.sleep_ms(20)
        nps.clear()
        nps.write()
        await asyncio.sleep_ms(5_000)
    """

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
