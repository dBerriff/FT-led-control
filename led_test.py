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
    onboard = Led('LED', 100)
    onboard.set_dc_pc(20)  # duty-cycle percent
    # start blinking to demo multitasking
    task_blink = asyncio.create_task(onboard.blink(100))

    n_np = 1
    pin_number = 28
    nps = NPStrip(pin_number, n_np)
    colours = nps.COLOURS

    np_index = 0  # NeoPixel index in range 0 to n-1
    for colour in colours:
        nps.set_pixel_colour(np_index, colour)
        nps.write()
        await asyncio.sleep_ms(1000)
    for i in range(0x19, 0, -1):
        nps.set_pixel_rgb(np_index, (i, i, i))
        nps.write()
        await asyncio.sleep_ms(200)
    nps.set_pixel_colour(np_index, nps.BLK)
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
