# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import LedChannel
from colour_space import ColourSpace

# helper coroutines

async def blink(led_, dc_u8, n):
    """ coro: blink the LED n times at dc_u8 """
    dc = led_.u8_u16(dc_u8)
    led_.dc_u16 = dc
    for _ in range(n):
        led_.duty_u16(dc)
        await asyncio.sleep_ms(100)
        led_.duty_u16(0)
        await asyncio.sleep_ms(900)

async def fade_in(led_, dc_gamma_, lin_level_, period=1000):
    """ coro: fade-in from 0 to lin_level
        - lin_level is uncompensated linear u8 level
        - gamma compensation is applied to each setting
    """
    if lin_level_ == 0:
        return
    step_pause = period // lin_level_
    fade_dc = 0
    while fade_dc < lin_level_:
        led_.set_dc_u8(dc_gamma_[fade_dc])
        fade_dc += 1
        await asyncio.sleep_ms(step_pause)
    led_.dc_u16 = led_.u8_u16(dc_gamma_[lin_level_])
    led_.duty_u16(led_.dc_u16)

async def fade_out(led_, dc_gamma_, lin_level_, period=1000):
    """ coro: fade-out from lin_level to 0
        - lin_level is uncompensated linear u8 level
        - gamma compensation is applied to each setting
    """
    if lin_level_ == 0:
        return
    step_pause = period // lin_level_
    fade_dc = lin_level_
    while fade_dc > 0:
        led_.set_dc_u8(dc_gamma_[fade_dc])
        fade_dc -= 1
        await asyncio.sleep_ms(step_pause)
    led_.dc_u16 = 0
    led_.duty_u16(0)

async def twin_flash(led_1, led_2, level_, period_ms=500):
    """ coro: flash alternating leds every period """
    led_1.dc_u16 = led_1.u8_u16(level_)
    led_2.dc_u16 = led_1.dc_u16

    while True:
        led_1.turn_on()
        led_2.turn_off()
        await asyncio.sleep_ms(period_ms)
        led_1.turn_off()
        led_2.turn_on()
        await asyncio.sleep_ms(period_ms)


async def main():
    # build gamma-correction tuple
    dc_gamma = ColourSpace().RGB_GAMMA

    led_a = LedChannel(pwm_pin=10)
    led_a.set_dc_u16(0)
    print(f'led_a: {led_a}')
    led_b = LedChannel(pwm_pin=11)
    led_b.set_dc_u16(0)
    print(f'led_b: {led_b}')
    lin_level = 191
    level = dc_gamma[lin_level]
    print(f'linear level: {lin_level} gamma-compensated level: {level}')

    await asyncio.sleep_ms(200)
    print('blink')
    asyncio.create_task(blink(led_a, level, 5))
    asyncio.create_task(blink(led_b, level, 5))
    await asyncio.sleep_ms(6_000)
    
    print('fade in')
    await fade_in(led_a, dc_gamma, lin_level)
    print('fade in complete')
    await asyncio.sleep_ms(1_000)

    print('fade out')
    await fade_out(led_a, dc_gamma, lin_level)
    print('fade out complete')
    await asyncio.sleep_ms(1_000)

    print('twin flash')
    tf_task = asyncio.create_task(twin_flash(led_a, led_b, level))
    await asyncio.sleep_ms(5_000)
    tf_task.cancel()
    led_a.turn_off()
    led_b.turn_off()
    await asyncio.sleep_ms(1_000)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
