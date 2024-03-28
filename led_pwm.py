# pwm_channel.py
"""
    control a PWM output
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
    - f = 1000Hz is used, as in Pimoroni code
    - see: https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules_py/pimoroni.py
"""

from machine import Pin, PWM


class PimoroniRGB:
    """ Pimoroni class to set Plasma 2040 RGB LED """

    def __init__(self, r_gp=16, g_gp=17, b_gp=18):
        self.led_r = PWM(Pin(r_gp), freq=1000)
        self.led_g = PWM(Pin(g_gp), freq=1000)
        self.led_b = PWM(Pin(b_gp), freq=1000)

    def set_rgb_u8(self, r, g, b):
        """
            set 16-bit duty cycle from 8-bit RGB
            - Pimoroni Plasma RGB LEDs duty inversion
        """
        #  invert
        r = 255 - r
        g = 255 - g
        b = 255 - b
        self.led_r.duty_u16(r * 257)
        self.led_g.duty_u16(g * 257)
        self.led_b.duty_u16(b * 257)


class PWMLed(PWM):
    """
        Control PWM output
        - no parameter range checking
        - RP2040 PWM is set by 16-bit duty cycle (duty_16())
        - freq = 1000Hz matches Pimoroni default
        - self.dc_u16 stores last-set value
        - dc_u8 is user scaling [0...255]
        - dc_pc is user scaling [0...100]
    """

    # super() does not support keyword arguments
    def __init__(self, pin_):
        super().__init__(Pin(pin_))
        self.pin = pin_  # for debug
        self.freq(1000)
        self.duty_u16(0)
        self.dc_u16 = 0  # for off/on dc restore

    def set_dc_u16(self, dc_u16_):
        """ set PWM duty cycle and store value """
        self.duty_u16(dc_u16_)
        self.dc_u16 = dc_u16_

    def set_dc_u8(self, dc_u8_):
        """ set PWM duty cycle by 8-bit range """
        self.set_dc_u16(dc_u8_ * 257)

    def set_dc_pc(self, dc_pc_):
        """ set PWM duty cycle by percentage range """
        self.set_dc_u16(dc_pc_ * 65535 // 100)

    def turn_on(self):
        """ set channel on at self.dc_u16 """
        self.duty_u16(self.dc_u16)

    def turn_off(self):
        """ set channel off; do not change self.dc_u16 """
        self.duty_u16(0)


def main():
    """ """
    pass


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
