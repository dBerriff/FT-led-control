# np_strip_helper.py
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
        # flash 100 to 200 times at random level
        for _ in range(randrange(100, 200)):
            level = randrange(96, 192)
            nps[px_index] = cs.get_rgb(arc_rgb_, level)
            nps.write()
            await asyncio.sleep_ms(20)
        # fade out glow
        for level in range(128, -1, -1):
            nps[px_index] = cs.get_rgb(glow_rgb_, level)
            nps.write()
            await asyncio.sleep_ms(10)
        await asyncio.sleep_ms(randrange(1_000, 5_000))


async def np_twinkler(nps, cs, pixel_, play_ev):
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
    while play_ev.is_set():
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
        nps[pixel_] = cs.get_rgb(lamp_rgb, level)
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


async def two_flash(nps, base_index, rgb, flash_ev, period=1000):
    """ flash 2 pixels alternatively
        - flash_ev is an asyncio.Event() to switch flashing on/off
    """
    
    def set_display(rgb_0, rgb_1):
        """ set the 2 pixels """
        nps[base_index] = rgb_0
        nps[bi_1] = rgb_1
        nps.write()
        
    off = (0, 0, 0)
    hold = period // 2
    bi_1 = base_index + 1
    write_delay_ms = 2  # allow PIO write to complete
    while True:
        set_display(off, off)
        await asyncio.sleep_ms(write_delay_ms)
        await flash_ev.wait()  # pass-through or wait for set()
        set_display(rgb, off)
        await asyncio.sleep_ms(hold)
        set_display(off, rgb)
        await asyncio.sleep_ms(hold)
    