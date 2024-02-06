# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import Led
from rgb_fns import get_rgb_gamma

async def twin_flash(led_1, led_2, level_, period_ms):
    """ flash alternating leds every period """
    led_1.dc_u16 = led_1.u8_u16(level_)
    led_2.dc_u16 = led_1.dc_u16

    for _ in range(20):
        led_1.turn_on()
        led_2.turn_off()
        await asyncio.sleep_ms(period_ms)
        led_1.turn_off()
        led_2.turn_on()
        await asyncio.sleep_ms(period_ms)
    led_2.turn_off()


async def main():

    led_a = Led(pwm_pin=9)
    led_a.set_dc_u16(0)
    led_b = Led(pwm_pin=10)
    led_b.set_dc_u16(0)

    await asyncio.sleep_ms(200)
    await led_a.blink(255, 5)
    await asyncio.sleep_ms(1000)
    
    await led_a.fade_in(255, 10_000)
    print('fade in complete')
    await asyncio.sleep_ms(1000)
    await led_a.fade_out(10_000)
    print('fade out complete')
    await asyncio.sleep_ms(1000)
    await twin_flash(led_a, led_b, 127, 500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
