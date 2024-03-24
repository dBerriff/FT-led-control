# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from np_strip_helper import mono_chase, colour_chase, two_flash


async def main():
    """ coro: test NeoPixel strip helper functions """

    # Pimoroni Plasma 2040 is hardwired to GPIO 15
    pin_number = 15
    n_pixels = 30
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()
    
    h = 270
    h_delta = 90
    s = 0.75
    s_delta = 0
    v = 0.75
    v_delta = -0.25

    for p in range(101):
        h_ = h + int(p * h_delta / 100)
        s_ = s + p * s_delta / 100
        v_ = v + p * v_delta / 100
        print(h_, s_, v_)
        rgb = cs.get_hsv_rgb(h_, s_, v_)
        rgb1 = cs.get_rgb_g(rgb)
        print('Set strip', h_, rgb, rgb1)

        nps.fill_array(rgb1)
        nps.write()
        await asyncio.sleep_ms(100)

    s = s_
    v = v_
    s_delta = -s_
    v_delta = -0.35
    for p in range(101):
        s_ = s + p * s_delta / 100
        v_ = v + p * v_delta / 100
        print(h_, s_, v_)
        rgb = cs.get_hsv_rgb(h_, s_, v_)
        rgb1 = cs.get_rgb_g(rgb)
        print('Set strip', h_, rgb, rgb1)

        nps.fill_array(rgb1)
        nps.write()
        await asyncio.sleep_ms(100)

    await asyncio.sleep_ms(5_000)
    nps.clear()
    nps.write()
    await asyncio.sleep_ms(200)

    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
