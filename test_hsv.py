# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
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

    level = 128
    rgb = cs.get_rgb_lg(cs.colours['orange'], level)
    nps.set_strip(rgb)
    nps.write()
    await asyncio.sleep_ms(1000)

    # shift grb_ to red and darken
    h = 270
    h_init = h
    h_delta = 90
    s = 0.9
    s_init = s
    s_delta = -0.2
    v_init = 0.95
    v_delta = -0.25
    for p in range(101):
        h = h_init + p * h_delta / 100
        s = s_init + p * s_delta / 100
        v = v_init + p * v_delta / 100
        rgb = cs.get_hsv_rgb(h/360.0, s, v)
        rgb1 = cs.get_rgb_g(rgb)
        print(f'h: {h} s: {s} v: {v} rgb: {rgb}')
        nps.set_strip(rgb1)
        nps.write()
        await asyncio.sleep_ms(100)

    # hold hue, reduce saturation and value
    s_init = s
    v_init = v
    s_delta = -s
    v_delta = -0.35
    for p in range(101):
        s = s_init + p * s_delta / 100
        v = v_init + p * v_delta / 100
        rgb = cs.get_hsv_rgb(h/360.0, s, v)
        rgb1 = cs.get_rgb_g(rgb)
        print(f'h: {h} s: {s} v: {v} rgb: {rgb}')
        nps.set_strip(rgb1)
        nps.write()
        await asyncio.sleep_ms(100)

    await asyncio.sleep_ms(10_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
