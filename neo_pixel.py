# led.py

""" LED-related classes """

import asyncio
from micropython import const
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
from pwm_led import PwmChannel
from neopixel import NeoPixel


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
