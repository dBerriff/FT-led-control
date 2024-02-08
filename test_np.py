# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelStrip
from colour_space import ColourSpace
import time
from random import randrange


# helper functions

async def cycle_pixel(nps_, index_, colours_, level_):
    """ coro: cycle pixel through colour set """
    for colour in colours_:
        nps_[index_] = colour.get_rgb(level_)
        nps_.write()
        await asyncio.sleep_ms(500)


async def time_fill_strip(nps_, rgb_):
    """ coro: test and time fill-strip method """
    print('Fill strip')
    c_time = time.ticks_us()
    nps_.fill_strip(rgb_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    await asyncio.sleep_ms(2_000)


async def cycle_colours(nps_, rgb_set_, reverse=False):
    """ coro: step through strip, cycling colour """
    level = 63
    c_mod = len(rgb_set_)
    c_0_index = 0
    for _ in range(100):
        c_index = c_0_index
        for np_index in range(nps_.n):
            nps_[np_index] = rgb_set_[c_index]
            c_index = (c_index + 1) % c_mod
        nps_.write()
        if reverse:
            c_0_index = (c_0_index + 1) % c_mod
        else:
            c_0_index = (c_0_index - 1) % c_mod
        await asyncio.sleep_ms(200)


async def np_arc_weld(nps_, cs_, arc_rgb_, glow_rgb_, pixel_):
    """ coro: simulate arc-weld flash and decay """
    for _ in range(2):
        for _ in range(randrange(100, 200)):
            level = randrange(127, 256)
            nps_[pixel_] = cs_.get_rgb(arc_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(20)
        for level in range(160, -1, -1):
            nps_[pixel_] = cs_.get_rgb(glow_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(10)
        await asyncio.sleep_ms(randrange(1_000, 5_000))


async def np_twinkler(nps_, pixel_):
    """ coro: simulate gas-lamp twinkle """
    lamp_rgb = (0xff, 0xcf, 0x9f)
    steady_level = 127
    dim_level = 95
    n_smooth = 5
    levels = [0] * n_smooth
    s_index = 0
    while True:
        twinkle = randrange(64)
        if randrange(0, 100):
            levels[s_index] = steady_level + twinkle
            level = sum(levels) // n_smooth
        else:
            for i in range(n_smooth):
                levels[i] = dim_level
            level = dim_level
        nps_[pixel_] = rgb_fns.get_rgb_l_g_c(lamp_rgb, level, rgb_gamma_)
        nps_.write()
        await asyncio.sleep_ms(randrange(20, 200))
        s_index += 1
        s_index %= 5


async def main():
    """ coro: test NeoPixel strip helper functions """

    pin_number = 28
    n_pixels = 300
    nps = PixelStrip(pin_number, n_pixels)
    cs = ColourSpace()

    level = 63  # 0 - 255
    rgb = cs.get_rgb('orange', level)
    arc_rgb = cs.colours['white']
    glow_rgb = cs.colours['red']

    await np_arc_weld(nps, cs, arc_rgb, glow_rgb, 0)

    await time_fill_strip(nps, rgb)
    await asyncio.sleep_ms(200)
    nps.clear()
    await asyncio.sleep_ms(200)

    """
    for dim in range(level, 0, -1):
        rgb = rgb_fns.get_rgb_l_g_c(c_rgb, dim, rgb_gamma)
        nps.fill_strip(rgb)
        nps.write()
        if rgb == (0, 0, 0):
            break
        await asyncio.sleep_ms(2)
    nps.fill_strip(off)
    nps.write()
    await asyncio.sleep_ms(200)
    
    rgb = rgb_fns.get_rgb_l_g_c(c_rgb, level, rgb_gamma)
    for i in range(120):
        nps.fill_range(i, 5, rgb)
        nps.write()
        await asyncio.sleep_ms(20)
        nps.fill_range(i, 5, off)
        nps.write()
        await asyncio.sleep_ms(2)

    rgb_list = tuple([
        rgb_fns.get_rgb_l_g_c(colours['red'], level, rgb_gamma),
        rgb_fns.get_rgb_l_g_c(colours['green'], level, rgb_gamma),
        rgb_fns.get_rgb_l_g_c(colours['blue'], level, rgb_gamma)
        ])
    for i in range(240):
        nps.fill_range_list(i, 3, rgb_list)
        nps.write()
        await asyncio.sleep_ms(20)
        nps.fill_range(i, 3, off)
        nps.write()
        await asyncio.sleep_ms(2)
    """

    c_names = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    cycle_set = [cs.get_rgb(name, level) for name in c_names]
    await cycle_colours(nps, cycle_set, True)

    nps.clear()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
