# pwm_channel.py
"""
    control a PWM output
    - developed using MicroPython v1.22.0
    - for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""
# !!! fix to match changes in colour_space !!!
# !!! combine classes for single level of inheritance !!!
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

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.freq(frequency)

    @property
    def dc_u16(self):
        return self._dc_u16

    @dc_u16.setter
    def dc_u16(self, dc_):
        self._dc_u16 = dc_

    def set_dc_u16(self, dc_u16_):
        """ set PWM duty cycle """
        self.duty_u16(dc_u16_)
        self.dc_u16 = dc_u16_

    def turn_on(self):
        """ turn channel on at set duty cycle """
        self.duty_u16(self._dc_u16)

    def turn_off(self):
        """ set channel off """
        self.duty_u16(0)
 
 
class Led(PwmChannel):
    """ pin-driven LED
        - intensity levels are 0 to 255, 8-bit register
    """

    def __init__(self, pwm_pin, frequency=800):
        super().__init__(Pin(pwm_pin), frequency)
        self.dc_u8 = 0
        self.dc_gamma = get_rgb_gamma()

    @staticmethod
    def u8_u16(dc_u8_):
        """ convert 8-bit to proportional 16-bit level for PWM """
        dc_u8_ = max(dc_u8_, 0)
        dc_u8_ = min(dc_u8_, 255)
        return (dc_u8_ << 8) + dc_u8_

    def set_dc_u8(self, dc_u8_):
        """ set LED u16 duty cycle from u8 """
        self.dc_u8 = dc_u8_
        dc_gc = self.dc_gamma[dc_u8_]
        self.set_dc_u16(self.u8_u16(dc_gc))

    async def blink(self, dc_u8, n):
        """ coro: blink the LED n times at set dc """
        self.dc_u8 = dc_u8
        dc_u16 = self.u8_u16(self.dc_gamma[dc_u8])
        for _ in range(n):
            self.set_dc_u16(dc_u16)
            await asyncio.sleep_ms(100)
            self.set_dc_u16(0x0000)
            await asyncio.sleep_ms(900)

    async def fade_in(self, dc_u8, period=1000):
        """ fade-in to set dc """
        step_pause = period // dc_u8
        dc = 0
        while dc < dc_u8:
            self.set_dc_u8(dc)
            dc += 1
            await asyncio.sleep_ms(step_pause)
        self.set_dc_u8(dc_u8)

    async def fade_out(self, period=1000):
        """ fade-out to set dc% """
        step_pause = period // self.dc_u8
        dc = self.dc_u8
        while dc > 0:
            self.set_dc_u8(dc)
            dc -= 1
            await asyncio.sleep_ms(step_pause)
        self.set_dc_u8(0)
