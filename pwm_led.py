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

    def __init__(self, pwm_pin, frequency=800):
        super().__init__(Pin(pwm_pin), frequency)
        self.name = str(pwm_pin)
        # self.blink_lock = asyncio.Lock()

    def set_dc_u16(self, dc_u16_):
        """ set LED duty cycle """
        self.duty_u16(dc_u16_)
        self._dc_u16 = dc_u16_

    def set_dc_pc(self, dc_pc_):
        """ set LED duty cycle """
        self.duty_u16(self.pc_u16(dc_pc_))
        self._dc_u16 = dc_pc_

    async def blink(self, dc_pc_, n):
        """ coro: blink the LED n times at set dc """
        level = self.pc_u16(dc_pc_)
        for _ in range(n):
            self.set_dc_u16(level)
            await asyncio.sleep_ms(100)
            self.set_dc_u16(0x0000)
            await asyncio.sleep_ms(900)
