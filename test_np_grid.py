# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from neo_pixel import NPStrip

import time


async def main():
    """ set NeoPixel values on grid """
    
    OFF = (0, 0, 0)
    
    async def cycle_pixel(index):
        """ cycle pixel through colour set """
        for colour in ('red', 'green', 'blue'):
            nps[index] = nps.get_rgb_l_g_c(colours[colour], level)
            nps.write()
            await asyncio.sleep_ms(100)
        nps[index] = OFF
        nps.write()

    # correct grid addressing scheme
    pixel_dict = {}
    for col in range(8):
        for row in range(8):
            if col % 2:
                r = 7 - row
            else:
                r = row
            pixel_dict[col, row] = col * 8 + r

    pin_number = 27
    n_np = 64  # number of NeoPixels
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours
    # level defines brightness with respect to 255 peak
    level = 127

    # step through grid
    for col in range(8):
        for row in range(8):
            await cycle_pixel(pixel_dict[col, row])

    # step through diagonal
    for col in range(8):
        row = col
        await cycle_pixel(pixel_dict[col, row])
        await asyncio.sleep_ms(10)

    # step through diagonal
    for col in range(7, -1, -1):
        row = 7 - col
        await cycle_pixel(pixel_dict[col, row])
        await asyncio.sleep_ms(10)


    # set colour of single NeoPixel; whole strip must be written
    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
