# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import PixelStrip

import time


async def main():
    """ blink onboard LED and set NeoPixel values """
    
    async def cycle_pixel(index):
        """ cycle pixel through colour set """

        for colour in colours:
            nps[index] = nps.get_rgb_l_g_c(colours[colour], level)
            nps.write()
            print(f'{colour}: {nps[np_index]}')
            await asyncio.sleep_ms(500)

    async def test_fill_strip(n_pixels):
        """ test and time fill-strip method """
        return  # make sure adequate current can be supplied
        print('Fill strip')
        colour = 'white'
        c_time = time.ticks_us()
        nps.strip_fill_rgb((0, 0, 0))
        print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
        c_time = time.ticks_us()
        nps.write()
        print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
        await asyncio.sleep_ms(2_000)

    # set onboard LED to blink to demo multitasking
    led_f = 800  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    task_blink = asyncio.create_task(onboard.blink(100))

    pin_number = 27
    n_np = 64  # number of NeoPixels
    nps = PixelStrip(pin_number, n_np)
    colours = nps.Colours
    np_index = 8  # use first pixel for tests

    # level defines brightness with respect to 255 peak
    level = 127

    # set colour of single NeoPixel; whole strip must be written

    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
