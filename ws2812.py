# ws2812.py
"""
    Classes:

    Ws2812
    Set pixel output for WS2812 LEDs (NeoPixels) by PIO state machine
    WS2812 pixel words are coded as 32-bit GRBW with W = 0
    W (white) byte is added by left-shift in PIO 'put'
    - there should be a 50µs pause between strip writes: normal awaits exceed this
    - thanks to MERG member Paul Redhead for information on PIO.
"""

import rp2
from machine import Pin
import array
from micropython import const
from colour_space import ColourSpace


class Ws2812:
    """
        Implement WS2812 driver using RP2040 programmable i/o
        See:
        - R Pi Pico C SDK: section 3.2.2
        - R Pi [Micro]Python SDK: section 3.9.2
        - https://tutoduino.fr/en/pio-rp2040-en/ for PIO code
    """

    GRBW_SHIFT = const(8)  # shift GRB to MSBytes in 32-bit word

    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW,
                 out_init=rp2.PIO.OUT_LOW,
                 out_shiftdir=rp2.PIO.SHIFT_LEFT,
                 autopull=True, pull_thresh=24)
    def ws2812():
        wrap_target()
        out(x, 1)
        set(pins, 1) [1]
        mov(pins, x) [1]
        set(pins, 0)
        wrap()

    def __init__(self, pin, n_pixels_):
        f_ = 5_000_000  # this version
        self.pin = pin  # for trace/debug
        self.n_pixels = n_pixels_
        self.n = n_pixels_
        self.sm = rp2.StateMachine(0, Ws2812.ws2812, freq=f_,
                                   set_base=Pin(pin), out_base=Pin(pin))
        self.arr = array.array('I', [0]*n_pixels_)
        self.cs = ColourSpace()
        # start state machine
        self.sm.active(True)

    def write(self):
        """ 'put' GRB array into StateMachine Tx FIFO """
        # shift moves rgb bits to MSB position
        self.sm.put(self.arr, self.GRBW_SHIFT)

    @staticmethod
    def encode_rgb(rgb_):
        """ encode rgb as single 24-bit GRB word """
        return (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    @staticmethod
    def encode_f(rgb_):
        """ encode rgb[0...1.0] as single 24-bit GRB word """
        return (int(rgb_[1] * 255) << 16) + (int(rgb_[0] * 255) << 8) + int(rgb_[2] * 255)

