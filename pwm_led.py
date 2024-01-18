# pwm_channel.py
"""
    control a PWM output
    - developed using MicroPython v1.22.0
    - for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""

import asyncio
from machine import Pin, PWM


class PwmChannel:
    """
    Control PWM output
        - frequency and duty cycle: no range checking
        - set_dc_u16() stores duty cycle; does not change state
        - call set_on() for output
    """

    def __init__(self, pwm_pin, frequency):
        self.channel = PWM(Pin(pwm_pin), freq=frequency, duty_u16=0)
        self._dc_u16 = 0

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.channel.freq(frequency)

    def set_dc_u16(self, dc_u16):
        """ set duty cycle by 16-bit unsigned integer """
        self._dc_u16 = dc_u16

    def set_on(self):
        """ set channel on """
        self.channel.duty_u16(self._dc_u16)

    def set_off(self):
        """ set channel off """
        self.channel.duty_u16(0)
 
 
class Led(PwmChannel):
    """ pin-driven LED """

    @staticmethod
    def pc_u16(percentage):
        """ convert positive percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    def __init__(self, pwm_pin, frequency):
        super().__init__(Pin(pwm_pin), frequency)
        self.name = str(pwm_pin)
        # self.blink_lock = asyncio.Lock()

    def set_dc_pc(self, percent):
        """ set LED duty cycle """
        self._dc_u16 = self.pc_u16(percent)

    async def flash(self, ms_=500):
        """ coro: flash the LED """
        self.set_on()
        await asyncio.sleep_ms(ms_)
        self.set_off()
        await asyncio.sleep_ms(ms_)

    async def blink(self, n):
        """ coro: blink the LED n times """
        for _ in range(n):
            self.set_on()
            await asyncio.sleep_ms(100)
            self.set_off()
            await asyncio.sleep_ms(900)
