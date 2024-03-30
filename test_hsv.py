# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pixel_strip import PixelStrip
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812


async def main():
    """ coro: test NeoPixel strip helper functions """

    n_pixels = 30
    # set board and strip chipset methods
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    cs = ColourSpace()
    nps = PixelStrip(driver, n_pixels)

    level = 128
    clr_u24 = nps.encode_rgb(cs.get_rgb_lg('orange', level))
    print(clr_u24)
    nps.set_strip(clr_u24)
    nps.write()
    await asyncio.sleep_ms(1000)

    # shift RGB to red and darken
    h = 270
    h_init = h
    h_delta = 90
    s = 0.9
    s_init = s
    s_delta = -0.2
    v_init = 0.95
    v_delta = -0.40
    # work in RGB for analysis
    for p in range(101):
        h = h_init + p * h_delta / 100
        s = s_init + p * s_delta / 100
        v = v_init + p * v_delta / 100
        rgb = cs.hsv_rgb_u8(h / 360.0, s, v)
        rgb_g = cs.get_rgb_g(rgb)
        print(f'h: {h} s: {s} v: {v} rgb: {rgb}')
        nps.set_strip_rgb(rgb_g)
        nps.write()
        await asyncio.sleep_ms(50)

    # hold hue, reduce saturation and value
    s_init = s
    v_init = v
    s_delta = -s_init
    v_delta = -0.35
    # work in RGB for analysis
    for p in range(100):
        s = s_init + p * s_delta / 99.0
        v = v_init + p * v_delta / 99.0
        rgb = cs.hsv_rgb_u8(h / 360.0, s, v)
        rgb_g = cs.get_rgb_g(rgb)
        print(f'h: {h} s: {s} v: {v} rgb: {rgb}')
        nps.set_strip_rgb(rgb_g)
        nps.write()
        await asyncio.sleep_ms(50)

    await asyncio.sleep_ms(5_000)
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
