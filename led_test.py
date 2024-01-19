# led.py

""" LED-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import NPStrip


async def main():
    """
        test LED methods
        - NeoPixel display uses MicroPython library
    """

    async def dim(nps_, pixel, rgb_, level_):
        """ dim pixel to zero """
        while level_ > 0:
            nps_.set_pixel_rgb(pixel, rgb_, level_)
            nps_.write()
            await asyncio.sleep_ms(20)
            level_ -= 1

    led_f = 400  # to match typical NeoPixel strip
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    # start blinking to demo multitasking
    task_blink = asyncio.create_task(onboard.blink(100))

    n_np = 1000  # number of NeoPixels
    pin_number = 28
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours

    print('Fill strip')
    nps.strip_fill_rgb(colours['white'], 31)
    nps.write()
    print('finished')
    np_index = 0  # NeoPixel index in range 0 to n-1
    # level defines brightness with respect to 255 peak
    level = 127
    for colour in colours:
        nps.set_pixel_rgb(np_index, colours[colour], level)
        print(f'{colour} gamma corrected: {nps.get_gamma_rgb(colours[colour], level)}')
        nps.write()
        await asyncio.sleep_ms(2_000)

    colour = 'white'
    print(f'{colour} gamma corrected: {nps.get_gamma_rgb(colours[colour], level)}')
    await dim(nps, np_index, colours['white'], level)
    nps.set_pixel_rgb(np_index, colours['black'], level)
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
