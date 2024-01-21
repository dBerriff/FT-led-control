# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import NPStrip

import time


async def main():
    """ blink onboard LED and set NeoPixel values """

    def rgb_gamma(rgb_, level_):
        """ return level and gamma adjusted rgb """
        rgb_l = nps.get_rgb_level(rgb_, level_)
        return nps.get_rgb_g_corrected(rgb_l)
               
    # set onboard LED to blink to demo multitasking
    led_f = 800  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    task_blink = asyncio.create_task(onboard.blink(100))

    pin_number = 28
    n_np = 500  # number of NeoPixels
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours
    np_index = 0  # for testing use first pixel

    # level defines brightness with respect to 255 peak
    level = 127

    print('Fill strip')
    c_time = time.ticks_us()
    rgb = rgb_gamma(colours['white'], level)
    nps.strip_fill_rgb(rgb)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    time.sleep_ms(1000)

    # set colour of single NeoPixel; whole strip must be written
    for colour in colours:
        nps[np_index] = rgb_gamma(colours[colour], level)
        nps.write()
        print(f'{colour}: {nps[np_index]}')
        await asyncio.sleep_ms(500)

    # test dim() coro
    colour = 'white'
    # dim() adds gamma correction
    await nps.dim_g(np_index, colours[colour], level)

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
