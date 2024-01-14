# led.py

""" LED-related classes """

import asyncio
from pwm_channel import PwmChannel


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
        super().__init__(pwm_pin, frequency)
        self.on = False
        self.blink_lock = asyncio.Lock()

    def set_on_pc(self, percent):
        """ turn LED on """
        self._dc_16 = self.pc_u16(percent)
        self.set_dc_u16(self._dc_16)
        self.on = True

    def set_off(self):
        """ turn LED off """
        self._dc_16 = 0
        self.set_dc_u16(0)
        self.on = False

    async def flash(self, ms_=500):
        """ coro: flash the LED """
        self.set_on_pc(self.dc_16)
        await asyncio.sleep_ms(ms_)
        self.set_off()
        await asyncio.sleep_ms(ms_)

    async def blink(self, n):
        """ coro: blink the LED n times """
        async with self.blink_lock:
            for _ in range(n):
                await asyncio.sleep_ms(900)
                self.set_on_pc(self.pc_u16)
                await asyncio.sleep_ms(100)
                self.set_off()
            await asyncio.sleep_ms(500)


async def main():
    """ test motor methods """

    params = {
        'pwm_pin': 2,
        'run_btn': 20,
        'kill_btn': 22,
        'pulse_f': 100,
        'motor_min_pc': 5,
        'motor_a_speed': {'F': 100, 'R': 95},
        'motor_b_speed': {'F': 95, 'R': 95},
        'motor_hold_period': 5
    }

    led_channel = Led(params['pwm_pin'], params['pulse_f'])
    led_channel.set_on_pc(5)
    print(led_channel._dc_16)
    await asyncio.sleep(2)
    led_channel.set_on_pc(10)
    print(led_channel._dc_16)
    await asyncio.sleep(2)
    led_channel.set_on_pc(20)
    print(led_channel._dc_16)
    await asyncio.sleep(2)
    led_channel.set_on_pc(100)
    print(led_channel._dc_16)
    await asyncio.sleep(5)
    led_channel.set_off()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
