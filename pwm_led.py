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


# !!! rename
class LedChannel(PWM):
    """
    Control PWM output
        - frequency and duty cycle: no range checking
        - preset_dc_u16() stores the set duty cycle;
          does not change state
        - call set_on() for output
    """

    # inheritance: MicroPython does not support setting
    # freq and duty_u16 by super() keyword arguments
    # frequency: 800Hz and 400Hz are most common for NeoPixels
    def __init__(self, pwm_pin, frequency=800):
        super().__init__(Pin(pwm_pin))
        self.freq(frequency)
        self.duty_u16(0)
        self.pin = pwm_pin  # for debug
        self.dc_u16 = 0  # for fade and other algorithms

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.freq(frequency)

    def set_dc_u16(self, dc_u16_):
        """ set PWM duty cycle and store value """
        self.duty_u16(dc_u16_)
        self.dc_u16 = dc_u16_

    def set_off(self):
        """ set 0 PWM duty cycle and store value """
        self.duty_u16(0)
        self.dc_u16 = 0

    def turn_on(self):
        """ turn channel on at stored duty cycle """
        self.duty_u16(self.dc_u16)

    def turn_off(self):
        """ set channel off """
        self.duty_u16(0)
 
    @staticmethod
    def u8_u16(dc_u8_):
        """ convert 8-bit to proportional 16-bit level """
        dc_u8_ = max(dc_u8_, 0)
        dc_u8_ = min(dc_u8_, 255)
        return (dc_u8_ << 8) + dc_u8_

    def set_dc_u8(self, dc_u8_):
        """ set LED u16 duty cycle from u8 """
        self.set_dc_u16(self.u8_u16(dc_u8_))
