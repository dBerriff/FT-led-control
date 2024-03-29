# pwm_channel.py
"""
    control a PWM output
    - developed for Famous Trains Derby by David Jones
    - shared with MERG by David Jones member 9042
    - f = 1000Hz is used, as in Pimoroni code
    - see: https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules_py/pimoroni.py
"""

from machine import Pin, PWM


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
