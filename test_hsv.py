# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pixel_strip import PixelStrip
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812


async def main():
    """ coro: test HSV method
        degrees
        000 - red
        060 - yellow
        120 - green
        180 - cyan
        240 - blue
        300 - magenta
    """

    n_pixels = 119
    # set board and strip chipset methods
    cs = ColourSpace()
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, n_pixels)
    # shift RGB to red and darken
    h = 240.0
    h_init = h
    h_delta = 359.0 - h
    s = 0.1
    s_init = s
    s_delta = 0.8
    v_init = 0.95
    v_delta = -0.50
    v = 0.0
    for p in range(101):
        h = h_init + p * h_delta / 100.0
        s = s_init + p * s_delta / 100.0
        v = v_init + p * v_delta / 100.0
        rgb = cs.hsv_rgb((h, s, v))
        print(f'h: {h} s: {s:.3f} v: {v:.3f} rgb: {rgb}')
        rgb_g = cs.rgb_g(rgb)
        nps.set_strip_rgb(rgb_g)
        nps.write()
        await asyncio.sleep_ms(100)

    # hold hue, reduce saturation and value
    s_init = s
    v_init = v
    s_delta = -2 * s
    v_delta = -0.2
    # work in RGB for analysis
    for p in range(100):
        s = max(s_init + p * s_delta / 99.0, 0.0)
        v = max(v_init + p * v_delta / 99.0, 0.25)
        rgb = cs.hsv_rgb((h, s, v))
        print(f'h: {h} s: {s:.3f} v: {v:.3f} rgb: {rgb}')
        rgb_g = cs.rgb_g(rgb)
        nps.set_strip_rgb(rgb_g)
        nps.write()
        await asyncio.sleep_ms(100)

    await asyncio.sleep_ms(6_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
