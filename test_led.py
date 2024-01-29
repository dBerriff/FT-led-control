# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import PixelStrip

import time


def blank_strip(strip):
    """ fill grid with (0, 0, 0) and pause """
    strip.fill_strip(strip.OFF)
    strip.write()


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
    
    async def cycle_pixel(index, colours_):
        """ cycle pixel through colour set """
        for colour in colours_:
            nps[index] = nps.get_rgb_l_g_c(colours_[colour], level)
            nps.write()
            await asyncio.sleep_ms(500)

    async def test_fill_strip(rgb_):
        """ test and time fill-strip method """
        print('Fill strip')
        c_time = time.ticks_us()
        nps.fill_strip(rgb_)
        print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
        c_time = time.ticks_us()
        nps.write()
        print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
        await asyncio.sleep_ms(2_000)

    # set onboard LED to blink to demo multitasking
    led_f = 800  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_u16(onboard.pc_u16(20))  # duty-cycle percent
    asyncio.create_task(onboard.blink(100))

    pin_number = 27
    nps = PixelStrip(pin_number, 30)
    colours = nps.Colours
    # level: intensity in range 0 to 255
    level = 63
    rgb = nps.get_rgb_l_g_c(colours['orange'], level)

    await test_fill_strip(rgb)
    await asyncio.sleep_ms(200)
    blank_strip(nps)

    cycle_set = 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
    rgb_set = [colours[c] for c in cycle_set]
    rgb_set = tuple([nps.get_rgb_l_g_c(c, level) for c in rgb_set])
    await cycle_colours(nps, rgb_set, True, 200)
    await asyncio.sleep_ms(200)
    blank_strip(nps)
    await cycle_colours(nps, rgb_set, False, 200)
    await asyncio.sleep_ms(200)
    blank_strip(nps)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
