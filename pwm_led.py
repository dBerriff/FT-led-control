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
        self.pin = pwm_pin  # for debug
        self._dc_u16 = 0

    @staticmethod
    def pc_u16(percentage):
        """ convert percentage to 16-bit equivalent """
        if 0 < percentage <= 100:
            return 0xffff * percentage // 100
        else:
            return 0

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.freq(frequency)

    @property
    def dc_u16(self):
        return self._dc_u16

    @dc_u16.setter
    def dc_u16(self, value):
        self._dc_u16 = value

    def set_dc_u16(self, dc_u16_):
        """ set LED duty cycle and turn on """
        self.duty_u16(dc_u16_)
        self.dc_u16 = dc_u16_

    def set_dc_pc(self, dc_pc_):
        """ set LED duty cycle and turn on """
        self.set_dc_u16(self.pc_u16(dc_pc_))

    def turn_on(self):
        """ turn channel on at set duty cycle """
        self.duty_u16(self._dc_u16)

    def turn_off(self):
        """ set channel off """
        self.duty_u16(0)
 
 
class Led(PwmChannel):
    """ pin-driven LED """

    def __init__(self, pwm_pin, frequency=800):
        super().__init__(Pin(pwm_pin), frequency)


    async def blink(self, dc_pc_, n):
        """ coro: blink the LED n times at set dc """
        dc_u16 = self.pc_u16(dc_pc_)
        for _ in range(n):
            self.set_dc_u16(dc_u16)
            await asyncio.sleep_ms(100)
            self.set_dc_u16(0x0000)
            await asyncio.sleep_ms(900)

    async def fade_in(self, dc_pc_):
        """ fade-in to set dc% """
        dc = 0
        target_dc = self.pc_u16(dc_pc_)
        while dc < target_dc:
            self.set_dc_u16(dc)
            dc += 100
            await asyncio.sleep_ms(20)
        self.set_dc_u16(target_dc)

    async def fade_out(self):
        """ fade-out to set dc% """
        dc = self._dc_u16
        target_dc = 0
        while dc > target_dc:
            self.set_dc_u16(dc)
            dc -= 100
            await asyncio.sleep_ms(20)
        self.set_dc_u16(target_dc)
