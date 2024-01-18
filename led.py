# led.py

""" LED-related classes """

import asyncio
from micropython import const
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
from pwm_channel import PwmChannel
from neopixel import NeoPixel
from time import sleep

class NPStrip(NeoPixel):
    """ extend NeoPixel class """
    
    Lev = const(0x19)
    WHT = (Lev, Lev, Lev)
    BLK = (0x00, 0x00, 0x00)
    RED = (Lev, 0x00, 0x00)
    GRN = (0x00, Lev, 0x00)
    BLU = (0x00, 0x00, Lev)
    CYN = (0x00, Lev, Lev)
    MGT = (Lev, 0x00, Lev)
    YEL = (Lev, Lev, 0x00)
    FLL = (0xff, 0xff, 0xff)
    COLOURS = {WHT, BLK, RED, GRN, BLU, CYN, MGT, YEL}


    def __init__(self, np_pin, n_pixels):
        super().__init__(Pin(np_pin, Pin.OUT), n_pixels)
        self.np_pin = np_pin
        self.n_pixels = n_pixels
        self.name = str(np_pin)
        self.n_pixels = n_pixels

    def set_pixel_colour(self, pixel, colour):
        """ set pixel 0 to n-1 to RGB colour """
        if colour in self.COLOURS:
            self[pixel] = colour

    def set_pixel_rgb(self, pixel, rgb):
        """ set pixel 0 to n-1 to RGB colour """
        self[pixel] = rgb

    """ from Raspberry Pi Pico Python SDK 3.9.2. WS2812 LED (NeoPixel) """
    @asm_pio(sideset_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
    def ws2812():
        T1 = 2
        T2 = 5
        T3 = 3
        wrap_target()
        label("bitloop")
        out(x, 1)               .side(0)    [T3 - 1]
        jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
        jmp("bitloop")          .side(1)    [T2 - 1]
        label("do_zero")
        nop()                   .side(0)    [T2 - 1]
        wrap()


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
        print(f'Pin {self.name} set to: {self._dc_u16}')

    async def flash(self, ms_=500):
        """ coro: flash the LED """
        self.set_on()
        await asyncio.sleep_ms(ms_)
        self.set_off()
        await asyncio.sleep_ms(ms_)

    async def blink(self, n):
        """ coro: blink the LED n times """
        print('Starting blink()')
        for _ in range(n):
            self.set_on()
            await asyncio.sleep_ms(100)
            self.set_off()
            await asyncio.sleep_ms(900)


async def main():
    """ test LED methods """
    
    onboard = Led('LED', 100)
    onboard.set_dc_pc(20)  # duty-cycle percent
    # start blinking to demo multitasking
    task_blink = asyncio.create_task(onboard.blink(100))

    n_np = 1
    pin_number = 28
    nps = NPStrip(pin_number, n_np)
    colours = nps.COLOURS

    np_index = 0  # NeoPixel index in range 0 to n-1
    for colour in colours:
        nps.set_pixel_colour(np_index, colour)
        nps.write()
        await asyncio.sleep_ms(1000)
    for i in range(0x19, 0, -1):
        nps.set_pixel_rgb(np_index, (i, i, i))
        nps.write()
        await asyncio.sleep_ms(200)
    nps.set_pixel_colour(np_index, nps.BLK)
    nps.write()
    task_blink.cancel()
    onboard.set_off()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
