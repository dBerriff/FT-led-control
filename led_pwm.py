# pwm_channel.py
"""
    control a PWM output
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
"""

from machine import Pin, PWM
import time


class RGBLed:
    """ Pimoroni class to set Plasma 2040 RGB LED """

    def __init__(self, r=16, g=17, b=18, invert=True):
        self.invert = invert
        self.led_r = PWM(Pin(r))
        self.led_r.freq(1000)
        self.led_g = PWM(Pin(g))
        self.led_g.freq(1000)
        self.led_b = PWM(Pin(b))
        self.led_b.freq(1000)

    def set_rgb(self, r, g, b):
        if self.invert:
            r = 255 - r
            g = 255 - g
            b = 255 - b
        self.led_r.duty_u16(int((r * 65535) / 255))
        self.led_g.duty_u16(int((g * 65535) / 255))
        self.led_b.duty_u16(int((b * 65535) / 255))


class LedPwm(PWM):
    """
    Control PWM output
        - frequency and duty cycle: no range checking
        - preset_dc_u16() stores the set duty cycle;
          does not change state
        - call set_on() for output
    """

    # super() does not support keyword arguments
    def __init__(self, pin_):
        super().__init__(Pin(pin_))
        self.freq(1000)
        self.duty_u16(0)
        self.pin = pin_  # for debug
        self.dc_u16 = 0  # for fade and other algorithms

    def reset_freq(self, frequency):
        """ reset PWM frequency """
        self.freq(frequency)

    def set_dc_u16(self, dc_u16_):
        """ set PWM duty cycle and store value """
        self.duty_u16(dc_u16_)
        self.dc_u16 = dc_u16_

    def set_dc_u8(self, dc_u8_):
        """ set PWM duty cycle and store value """
        self.set_dc_u16(dc_u8_ * 65535 // 255)

    def set_dc_pc(self, dc_pc_):
        """ set PWM duty cycle and store value """
        self.set_dc_u16(dc_pc_ * 65535 // 100)

    def turn_on(self):
        """ turn channel on at saved duty cycle """
        self.duty_u16(self.dc_u16)

    def turn_off(self):
        """ set channel off but save duty cycle """
        self.duty_u16(0)


def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    led = RGBLed(16, 17, 18)  # Plasma 2040

    led.set_rgb(0, 0, 0)
    time.sleep(1)

    led.set_rgb(128, 0, 0)
    time.sleep(1)
    led.set_rgb(0, 128, 0)
    time.sleep(1)
    led.set_rgb(0, 0, 128)
    time.sleep(1)

    led.set_rgb(0, 128, 128)
    time.sleep(1)
    led.set_rgb(128, 0, 128)
    time.sleep(1)
    led.set_rgb(128, 128, 0)
    time.sleep(1)

    led.set_rgb(0, 0, 0)
    time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
