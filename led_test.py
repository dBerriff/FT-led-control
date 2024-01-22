# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import NPStrip

import time


async def main():
    """ blink onboard LED and set NeoPixel values """
               
    # set onboard LED to blink to demo multitasking
    led_f = 800  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    task_blink = asyncio.create_task(onboard.blink(100))

    pin_number = 28
    n_np = 8  # number of NeoPixels
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours
    np_index = 0  # use first pixel for tests

    # level defines brightness with respect to 255 peak
    level = 127

    print('Fill strip')
    colour = 'white'
    c_time = time.ticks_us()
    nps.strip_fill_rgb((0, 0, 0))
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    nps.write()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    await asyncio.sleep_ms(2_000)

    # set colour of single NeoPixel; whole strip must be written
    for colour in colours:
        nps[np_index] = nps.get_rgb_l_g_c(colours[colour], level)
        nps.write()
        print(f'{colour}: {nps[np_index]}')
        await asyncio.sleep_ms(500)

    # test dim() coro
    colour = 'white'
    # dim() sets level and adds gamma correction
    await nps.dim_g_c(np_index, colours[colour], level)

    c_time = time.ticks_us()
    nps.strip_fill_rgb((0, 0, 0))
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
