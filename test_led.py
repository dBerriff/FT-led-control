# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import PixelStrip
import led

import time

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


async def cycle_colours(strip, rgb_set_, reverse=False, pause=20):
    """ step through strip, cycling colour """
    rgb_mod = len(rgb_set_)
    np_0_index = 0
    for _ in range(100):
        c_index = np_0_index
        for np_index in range(strip.n_pixels):
            strip[np_index] = rgb_set_[c_index]
            c_index = (c_index + 1) % rgb_mod
        strip.write()
        await asyncio.sleep_ms(pause)
        if reverse:
            np_0_index += 1
        else:
            np_0_index -= 1
        np_0_index %= rgb_mod


async def main():
    """ blink onboard LED and set NeoPixel values """

    pin_number = 27
    n_pixels = 30
    nps = PixelStrip(pin_number, n_pixels)
    colours = nps.Colours
    
    gamma = 2.6  # Adafruit suggestion
    rgb_gamma = led.get_rgb_gamma(2.6)  # conversion tuple
    level = 127  # 0 - 255
    c_rgb = colours['orange']
    rgb = led.get_rgb_l_g_c(c_rgb, level, rgb_gamma)

    await time_fill_strip(nps, rgb)
    await asyncio.sleep_ms(200)
    for dim in range(level, 0, -1):
        rgb = led.get_rgb_l_g_c(c_rgb, dim, rgb_gamma)
        nps.fill_strip(rgb)
        nps.write()
        if rgb == (0, 0, 0):
            break
        await asyncio.sleep_ms(2)
    nps.fill_strip(nps.OFF)
    nps.write()
    await asyncio.sleep_ms(200)
    
    rgb = led.get_rgb_l_g_c(c_rgb, level, rgb_gamma)
    for i in range(240):
        nps.fill_range(i, 5, rgb)
        nps.write()
        await asyncio.sleep_ms(20)
        nps.fill_range(i, 5, nps.OFF)
        nps.write()
        await asyncio.sleep_ms(2)

    cycle_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = [colours[c] for c in cycle_set]
    rgb_set = tuple([led.get_rgb_l_g_c(c, level, rgb_gamma) for c in rgb_set])
    await cycle_colours(nps, rgb_set, True, 50)
    await cycle_colours(nps, rgb_set, False, 50)
    await asyncio.sleep_ms(200)
    
    nps.fill_strip(nps.OFF)
    nps.write()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
