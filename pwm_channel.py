# pwm_channel.py
"""
    control a PWM output
    - developed using MicroPython v1.22.0
    - for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""

from machine import Pin, PWM


class PwmChannel:
    """
    Control PWM output
        - frequency and duty cycle: no range checking
        - set_dc_u16() stores duty cycle
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
 