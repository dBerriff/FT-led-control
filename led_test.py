# led.py

""" LED-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import NPStrip

import time


async def main():
    """
        test LED methods
        - NeoPixel display uses MicroPython library
    """

    async def dim(nps_, pixel, rgb_):
        """ dim pixel to zero """
        level_ = max(rgb_)
        while level_ > 0:
            rgb_c = nps_.get_rgb_g_corrected(rgb_, level_)
            nps_[pixel] = rgb_c
            nps_.write()
            await asyncio.sleep_ms(200)
            if rgb_c == (0, 0, 0):
                break
            level_ = max(rgb_c) - 1

    led_f = 800  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    # start blinking to demo multitasking
    task_blink = asyncio.create_task(onboard.blink(100))

    pin_number = 28
    n_np = 100  # number of NeoPixels
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours
    np_index = 0  # for testing use first pixel

    # level defines brightness with respect to 255 peak
    level = 127

    print('Fill strip')
    c_time = time.ticks_us()
    nps.strip_fill_rgb(colours['white'], level)
    print(f'filled: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps.write()
    print(f'written: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    
    # set colour of single NeoPixel; whole strip must be written
    for colour in colours:
        rgb = nps.get_rgb_g_corrected(colours[colour], level)
        nps[np_index] = rgb
        nps.write()
        print(f'{colour} level-set and gamma-corrected: {rgb}')
        await asyncio.sleep_ms(500)
    
    # test local dim coro
    colour = 'white'
    level = 255
    rgb = nps.get_rgb_g_corrected(colours[colour], level)
    print(f'{colour} level-set and gamma-corrected: {rgb}')
    await dim(nps, np_index, rgb)

    nps[np_index] = nps.get_rgb_level(colours['black'], 0)
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
