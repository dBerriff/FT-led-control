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


async def time_set_strip(nps_, rgb_, level_):
    """ coro: test and time fill-strip method """
    c_time = time.ticks_us()
    nps_.set_strip(rgb_, level_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


async def cycle_colours(nps_, c_set_, level_):
    """ coro: step through strip, cycling colour """
    c_mod = len(c_set_)
    c_index = 0
    for i in range(nps_.n):
        nps_.set_pixel(i, c_set_[c_index], level_) 
        c_index = (c_index + 1) % c_mod
        nps_.write()
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

    pin_number = 27
    n_pixels = 64
    nps = PixelStrip(pin_number, n_pixels)
    cs = ColourSpace()

    level = 64  # 0 - 255
    
    rgb = 'orange'

    print('set_pixel')
    nps.set_pixel(5, rgb, level)
    nps.write()
    await asyncio.sleep_ms(2000)
    nps.clear()

    print('set_strip')
    nps.set_strip(rgb, level)
    nps.write()
    await asyncio.sleep_ms(2000)
    nps.clear()

    print('set_range')
    nps.set_range(32, 16, rgb, level)
    nps.write()
    await asyncio.sleep_ms(2000)
    nps.clear()
    
    print('set_range_c_list')
    c_list = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    nps.set_range_c_list(32, 16, c_list, level)
    nps.write()
    await asyncio.sleep_ms(2000)
    
    print('time set_strip')
    await time_set_strip(nps, 'orange', level)
    await asyncio.sleep_ms(2000)    

    nps.clear()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
