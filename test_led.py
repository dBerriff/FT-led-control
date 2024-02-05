# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led

async def twin_flash(led_1, led_2, level_pc, period_ms):
    """ flash alternating leds every period """
    led_1.dc_u16 = led_1.pc_u16(level_pc)
    led_2.dc_u16 = led_1.dc_u16

    for _ in range(20):
        led_1.turn_on()
        led_2.turn_off()
        await asyncio.sleep_ms(period_ms)
        led_1.turn_off()
        led_2.turn_on()
        await asyncio.sleep_ms(period_ms)


async def main():
    """ blink onboard LED and set NeoPixel values """
    led_a = Led(9, 800)
    led_a.set_dc_pc(0)
    led_b = Led(10, 800)
    led_b.set_dc_pc(0)
    await asyncio.sleep_ms(200)
    await led_a.blink(100, 5)
    await asyncio.sleep_ms(1000)
    
    await led_a.fade_in(25)
    print('fade in complete')
    await asyncio.sleep_ms(1000)
    await led_a.fade_out()
    print('fade out complete')
    await asyncio.sleep_ms(1000)
    await twin_flash(led_a, led_b, 50, 500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
