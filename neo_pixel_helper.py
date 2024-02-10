# neo_pixel_helper.py
""" helper funcions for PixelStrip class """
import asyncio
from random import randrange


async def np_arc_weld(nps_, pixel_):
    """ coro: simulate arc-weld flash and decay """
    arc_rgb_ = 'white'
    glow_rgb_ = 'red'
    for _ in range(2):
        for _ in range(randrange(100, 200)):
            level = randrange(127, 256)
            nps_[pixel_] = nps_.get_rgb(arc_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(20)
        for level in range(160, -1, -1):
            nps_[pixel_] = nps_.get_rgb(glow_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(10)
        await asyncio.sleep_ms(randrange(1_000, 5_000))


async def np_twinkler(nps_, pixel_):
    """ coro: simulate gas-lamp twinkle """
    lamp_rgb = (0xff, 0xcf, 0x9f)
    base_level = 64
    dim_level = 95
    n_smooth = 3
    # levels list: take mean value
    levels = [0] * n_smooth
    l_index = 0
    for _ in range(100):
        twinkle = randrange(64, 128, 8)
        # randrange > 0; no 'pop'
        if randrange(0, 50) > 0:  # most likely
            levels[l_index] = base_level + twinkle
            level = sum(levels) // n_smooth
        # randrange == 0; 'pop'
        else:
            # set 'pop' across levels list
            for i in range(n_smooth):
                levels[i] = dim_level
            level = dim_level
        print(level)
        nps_[pixel_] = nps_.get_rgb(lamp_rgb, level)
        nps_.write()
        await asyncio.sleep_ms(randrange(20, 200, 20))
        l_index += 1
        l_index %= n_smooth
