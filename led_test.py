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

    async def dim(nps_, pixel, level):
        """ dim pixel to zero """
        while level > 0:
            nps_.set_pixel_rgb(pixel, (level, level, level))
            nps_.write()
            await asyncio.sleep_ms(20)
            level -= 1

    led_f = 400
    onboard = Led('LED', led_f)
    onboard.set_dc_pc(20)  # duty-cycle percent
    # start blinking to demo multitasking
    task_blink = asyncio.create_task(onboard.blink(100))

    n_np = 1
    pin_number = 28
    nps = NPStrip(pin_number, n_np)
    colours = nps.Colours

    np_index = 0  # NeoPixel index in range 0 to n-1
    for colour in colours:
        print(colour)
        nps.set_pixel_rgb(np_index, nps.colour_rgb(colour, 63))
        nps.write()
        await asyncio.sleep_ms(1000)

    c = (0xff // 2, 0xa5 // 2, 0x00 // 2)
    print(f'orange rgb: {c}')
    nps.set_pixel_rgb(np_index, c)
    nps.write()
    await asyncio.sleep_ms(2000)

    c = (0xff // 3, 0xc0 // 3, 0xcb // 3)
    print(f'pink rgb: {c}')
    nps.set_pixel_rgb(np_index, c)
    nps.write()
    await asyncio.sleep_ms(2000)

    await dim(nps, np_index, 127)
    nps.set_pixel_rgb(np_index, nps.colour_rgb('BLK', 0))
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
