# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pixel_strip import PixelStrip
from colour_space import ColourSpace
from plasma_2040 import Plasma2040


async def main():
    """ coro: test NeoPixel strip helper functions """

    # Pimoroni Plasma 2040 is hardwired to GPIO 15
    n_pixels = 30
    board = Plasma2040()
    ps = PixelStrip(board.DATA, n_pixels)
    cs = ColourSpace()

    level = 128
    rgb_u28 = ps.chipset.encode_rgb(
        cs.get_rgb_lg('orange', level))
    print(rgb_u28)
    ps.set_strip(rgb_u28)
    ps.chipset.write()
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
        ps.set_strip_rgb(rgb_g)
        ps.chipset.write()
        await asyncio.sleep_ms(50)

    # hold hue, reduce saturation and value
    s_init = s
    v_init = v
    s_delta = -s_init
    v_delta = -0.35
    # work in RGB for analysis
    for p in range(101):
        s = s_init + p * s_delta / 100
        v = v_init + p * v_delta / 100
        rgb = cs.hsv_rgb_u8(h / 360.0, s, v)
        rgb_g = cs.get_rgb_g(rgb)
        print(f'h: {h} s: {s} v: {v} rgb: {rgb}')
        ps.set_strip_rgb(rgb_g)
        ps.chipset.write()
        await asyncio.sleep_ms(50)

    await asyncio.sleep_ms(10_000)
    ps.clear_strip()
    ps.chipset.write()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
