# helper methods for Ws2812Strip

import asyncio
from random import randrange


async def np_arc_weld(nps, cs, px_index, play_ev):
    """ coro: drive a single pixel to simulate
        arc-weld flash and 'glow' decay
    """
    arc_rgb_ = 'white'
    glow_rgb_ = 'red'
    while play_ev.is_set():
        for _ in range(randrange(100, 200)):
            level = randrange(96, 192)
            nps[px_index] = cs.get_rgb(arc_rgb_, level)
            nps.write()
            await asyncio.sleep_ms(20)
        for level in range(128, -1, -1):
            nps[px_index] = cs.get_rgb(glow_rgb_, level)
            nps.write()
            await asyncio.sleep_ms(10)
        await asyncio.sleep_ms(randrange(1_000, 5_000))


async def np_twinkler(nps, pixel_):
    """ coro: single pixel:
        simulate gas-lamp twinkle
    """
    lamp_rgb = (0xff, 0xcf, 0x9f)
    base_level = 64
    dim_level = 95
    n_smooth = 3
    # levels list: take mean value
    levels = [0] * n_smooth
    l_index = 0
    while True:
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
        nps[pixel_] = nps.get_rgb(lamp_rgb, level)
        nps.write()
        await asyncio.sleep_ms(randrange(20, 200, 20))
        l_index += 1
        l_index %= n_smooth


async def mono_chase(nps, rgb_list, play_ev, pause=20):
    """ np strip:
        fill count_ pixels with list of rgb values
        - n_rgb does not have to equal count_
    """
    n_pixels = nps.n
    n_colours = len(rgb_list)
    index = 0
    while play_ev.is_set():
        for i in range(n_colours):
            nps[(index + i) % n_pixels] = rgb_list[i]
        nps.write()
        await asyncio.sleep_ms(pause)
        nps[index] = (0, 0, 0)
        index = (index + 1) % n_pixels


async def colour_chase(nps, rgb_list, pause=20):
    """ np strip:
        fill count_ pixels with list of rgb values
        - n_rgb does not have to equal count_
    """
    n_pixels = nps.n
    n_rgb = len(rgb_list)
    c_index = 0
    for _ in range(100):
        for i in range(n_pixels):
            nps[i] = rgb_list[(i + c_index) % n_rgb]
        nps.write()
        await asyncio.sleep_ms(pause)
        c_index = (c_index - 1) % n_rgb
