# led_test.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pwm_led import LedChannel
from colour_space import ColourSpace

# helper coroutines


async def fade_in(led_, dc_gamma_, lin_level_, period=1000):
    """ coro: fade-in from 0 to lin_level
        - lin_level is linear u8 level so that gamma
            compensation can be applied to each setting
    """
    if lin_level_ == 0:
        return
    step_pause = period // lin_level_
    fade_dc = 0
    while fade_dc < lin_level_:
        led_.set_dc_u8(dc_gamma_[fade_dc])
        fade_dc += 1
        await asyncio.sleep_ms(step_pause)
    led_.set_dc_u8(dc_gamma_[lin_level_])


async def fade_out(led_, dc_gamma_, lin_level_, period=1000):
    """ coro: fade-out from lin_level to 0
        - lin_level is linear u8 level so that gamma
            compensation can be applied to each setting
     """
    if lin_level_ == 0:
        return
    step_pause = period // lin_level_
    fade_dc = lin_level_
    while fade_dc > 0:
        led_.set_dc_u8(dc_gamma_[fade_dc])
        fade_dc -= 1
        await asyncio.sleep_ms(step_pause)
    led_.set_dc_u8(0)


async def blink(led_, dc_u8, n):
    """ coro: blink the LED n times at dc_u8 """
    dc_u16 = led_.u8_u16(dc_u8)
    for _ in range(n):
        led_.duty_u16(dc_u16)
        await asyncio.sleep_ms(100)
        led_.duty_u16(0)
        await asyncio.sleep_ms(900)


async def twin_flash(led_0, led_1, dc_u8, period_ms=500):
    """ coro: flash alternating leds every period at dc_u8 """
    # pre-set on level
    led_0.dc_u16 = led_0.u8_u16(dc_u8)
    led_1.dc_u16 = led_0.dc_u16

    while True:
        led_0.turn_on()
        led_1.turn_off()
        await asyncio.sleep_ms(period_ms)
        led_0.turn_off()
        led_1.turn_on()
        await asyncio.sleep_ms(period_ms)


async def main():
    # build gamma-correction tuple
    dc_gamma = ColourSpace().RGB_GAMMA

    led_pins = (10, 11, 12, 13, 14)
    led_list = [LedChannel(pwm_pin=p) for p in led_pins]
    for led in led_list:
        print(f'led: {led}')

    lin_level = 191
    level = dc_gamma[lin_level]
    print(f'linear level: {lin_level} gamma-compensated level: {level}')

    await asyncio.sleep_ms(200)
    print('blink')
    task_list = [blink(led, level, 5) for led in led_list]
    await asyncio.gather(*task_list)

    await asyncio.sleep_ms(1_000)
    
    print('fade in')
    await fade_in(led_list[0], dc_gamma, lin_level)
    await asyncio.sleep_ms(1_000)
    print('fade out')
    await fade_out(led_list[0], dc_gamma, lin_level)
    await asyncio.sleep_ms(1_000)

    print('twin flash')
    tf_task = asyncio.create_task(
        twin_flash(led_list[0], led_list[1], level))
    await asyncio.sleep_ms(5_000)

    tf_task.cancel()
    await asyncio.sleep_ms(20)
    for led in led_list:
        led.turn_off()
    await asyncio.sleep_ms(1_000)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
