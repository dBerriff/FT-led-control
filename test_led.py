# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from neo_pixel import PixelStrip
from pwm_led import Led
import led
import time
from random import randrange

# helper functions


async def cycle_pixel(nps_, index_, colours_, level_):
    """ cycle pixel through colour set """
    for colour in colours_:
        nps_[index_] = nps_.get_rgb_l_g_c(colours_[colour], level_)
        nps_.write()
        await asyncio.sleep_ms(500)


async def time_fill_strip(nps_, rgb_):
    """ test and time fill-strip method """
    print('Fill strip')
    c_time = time.ticks_us()
    nps_.fill_strip(rgb_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps_.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    await asyncio.sleep_ms(2_000)


async def cycle_colours(nps_, rgb_set_, reverse=False, pause=20):
    """ step through strip, cycling colour """
    rgb_mod = len(rgb_set_)
    np_0_index = 0
    for _ in range(100):
        c_index = np_0_index
        for np_index in range(nps_.n_pixels):
            nps_[np_index] = rgb_set_[c_index]
            c_index = (c_index + 1) % rgb_mod
        nps_.write()
        await asyncio.sleep_ms(pause)
        if reverse:
            np_0_index += 1
        else:
            np_0_index -= 1
        np_0_index %= rgb_mod

async def arc_weld(nps_, pixel_, rgb_gamma_):
    """ simulate arc-weld flash and decay """
    arc_rgb = (255, 255, 255)
    glow_rgb = (255, 0, 0)
    while True:
        for _ in range(randrange(100, 200)):
            level = randrange(127, 256)
            nps_[pixel_] = led.get_rgb_l_g_c(
                arc_rgb, level, rgb_gamma_)
            nps_.write()
            await asyncio.sleep_ms(20)
        for level in range(127, -1, -1):
            nps_[pixel_] = led.get_rgb_l_g_c(
                glow_rgb, level, rgb_gamma_)
            nps_.write()
            await asyncio.sleep_ms(20)
        await asyncio.sleep_ms(randrange(1000, 15000))

async def gl_twinkler(nps_, pixel_, rgb_gamma_):
    """ simulate gas-lamp twinkle """
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
        nps_[pixel_] = led.get_rgb_l_g_c(lamp_rgb, level, rgb_gamma_)
        nps_.write()
        await asyncio.sleep_ms(randrange(20, 200))
        s_index += 1
        s_index %= 5

async def main():
    """ blink onboard LED and set NeoPixel values """

    pin_number = 28
    n_pixels = 1
    nps = PixelStrip(pin_number, n_pixels)
    colours = nps.colours
    off = (0, 0, 0)
    
    gamma = 2.6  # Adafruit suggestion
    rgb_gamma = led.get_rgb_gamma(gamma)  # conversion tuple
    level = 127  # 0 - 255
    c_rgb = colours['orange']
    rgb = led.get_rgb_l_g_c(c_rgb, level, rgb_gamma)
    
    task_1 = asyncio.create_task(gl_twinkler(nps, 0, rgb_gamma))

    """
    await time_fill_strip(nps, rgb)
    await asyncio.sleep_ms(200)
    for dim in range(level, 0, -1):
        rgb = led.get_rgb_l_g_c(c_rgb, dim, rgb_gamma)
        nps.fill_strip(rgb)
        nps.write()
        if rgb == (0, 0, 0):
            break
        await asyncio.sleep_ms(2)
    nps.fill_strip(off)
    nps.write()
    await asyncio.sleep_ms(200)
    
    rgb = led.get_rgb_l_g_c(c_rgb, level, rgb_gamma)
    for i in range(120):
        nps.fill_range(i, 5, rgb)
        nps.write()
        await asyncio.sleep_ms(20)
        nps.fill_range(i, 5, off)
        nps.write()
        await asyncio.sleep_ms(2)

    rgb_list = tuple([
        led.get_rgb_l_g_c(colours['red'], level, rgb_gamma),
        led.get_rgb_l_g_c(colours['green'], level, rgb_gamma),
        led.get_rgb_l_g_c(colours['blue'], level, rgb_gamma)
        ])
    for i in range(240):
        nps.fill_range_list(i, 3, rgb_list)
        nps.write()
        await asyncio.sleep_ms(20)
        nps.fill_range(i, 3, off)
        nps.write()
        await asyncio.sleep_ms(2)
    cycle_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = [colours[c] for c in cycle_set]
    rgb_set = tuple([led.get_rgb_l_g_c(c, level, rgb_gamma) for c in rgb_set])
    await cycle_colours(nps, rgb_set, True, 50)
    await cycle_colours(nps, rgb_set, False, 50)
    await asyncio.sleep_ms(200)
    
    task_1.cancel()
    await asyncio.sleep_ms(20)
    nps.fill_strip(off)
    nps.write()
    await asyncio.sleep_ms(20)
"""
    led_ctrl = Led(9, 800)
    dc = 0
    while dc < 100:
        led_ctrl.set_dc_pc(dc)
        dc += 1
        await asyncio.sleep_ms(20)
    await asyncio.sleep_ms(1000)
    while dc > 0:
        led_ctrl.set_dc_pc(dc)
        dc -= 1
        await asyncio.sleep_ms(20)
    led_ctrl.set_dc_pc(0)
    await asyncio.sleep_ms(200)
    await led_ctrl.blink(100, 10)
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
