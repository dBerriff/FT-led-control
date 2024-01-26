# pwm_channel.py
"""
    control a PWM output
    - developed using MicroPython v1.22.0
    - for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""

import asyncio
from machine import Pin, PWM
from random import randrange


class PwmChannel(PWM):
    """
    Control PWM output
        - frequency and duty cycle: no range checking
        - preset_dc_u16() stores the set duty cycle;
          does not change state
        - call set_on() for output
    """

    def __init__(self, pwm_pin, frequency):
        super().__init__(Pin(pwm_pin))
        self.freq(frequency)
        self.duty_u16(0)
        self.pin = pwm_pin
        self._dc_u16 = 0

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.freq(frequency)

    def preset_dc_u16(self, dc_u16):
        """ set duty cycle by 16-bit unsigned integer """
        self._dc_u16 = dc_u16

    def set_on(self):
        """ set channel on """
        self.duty_u16(self._dc_u16)

    def set_off(self):
        """ set channel off """
        self.duty_u16(0)
 
 
class Led(PwmChannel):
    """ pin-driven LED """

    @staticmethod
    def pc_u16(percentage):
        """ convert percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    def __init__(self, pwm_pin, frequency):
        super().__init__(Pin(pwm_pin), frequency)
        self.name = str(pwm_pin)
        # self.blink_lock = asyncio.Lock()

    def set_dc_u16(self, dc_u16_):
        """ set LED duty cycle """
        self.duty_u16(dc_u16_)
        self._dc_u16 = dc_u16_

    async def flash_u16(self, flash_u16_, duration_ms=500):
        """ coro: flash the LED then restore dc """
        self.duty_u16(flash_u16_)
        await asyncio.sleep_ms(duration_ms)
        self.duty_u16(self._dc_u16)

    async def blink(self, n):
        """ coro: blink the LED n times at set dc """
        for _ in range(n):
            self.set_on()
            await asyncio.sleep_ms(100)
            self.set_off()
            await asyncio.sleep_ms(900)

    async def twinkle(self, steady_u16):
        """ replicate MERG gas-lamp twinkle
            - add/subract random values
        """
        while True:
            # sum(steady, twinkle(5 - 10s), pop(every 10s))
            pause = 5_000
            twinkle = steady_u16 // 3
            pop = steady_u16 // 2
            sum_u16 = steady_u16 + twinkle - pop
            self.duty_u16(sum_u16)
            await asyncio.sleep_ms(pause)
