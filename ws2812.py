# ws2812.py
"""
    Classes:

    Ws2812
    Set pixel output for WS2812 LEDs (NeoPixels) by PIO phase machine
    WS2812 pixel words are coded as 32-bit GRBW with W = 0
    W byte is added by left-shift in PIO 'put'
    - >= 50µs pause required between strip writes
        -- suggest include asyncio.sleep_ms(1) as a minimum
"""

import rp2
from machine import Pin
import array
from micropython import const


class Ws2812:
    """
        Implement WS2812 driver using RP2040 PIO
        See:
        - R Pi Pico C SDK: section 3.2.2
        - R Pi [Micro]Python SDK: section 3.9.2
        - https://tutoduino.fr/en/pio-rp2040-en/ for PIO code
        - n_pixels is set here so arr can be instantiated
    """

    GRB_SHIFT = const(8)  # shift 24-bit GRB colour into 32-bit word

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

    def __init__(self, pin):
        f_ = 5_000_000  # Hz
        self.pin = pin  # for trace/debug
        self.n_pixels = None
        self.arr = None
        self.sm = rp2.StateMachine(
            0, Ws2812.ws2812, freq=f_, set_base=Pin(pin), out_base=Pin(pin))

    def set_active(self, active=True):
        """ set sm active """
        self.sm.active(active)

    def write(self):
        """
            'put' colour array into StateMachine's Tx FIFO
            - shift moves GRB bytes to MSB position
            - sm autopull set True
        """
        self.sm.put(self.arr, self.GRB_SHIFT)

    def set_n_pixels(self, n_pixels_):
        """ set n_pixels and arr size """
        self.n_pixels = n_pixels_
        self.arr = array.array('I', [0]*n_pixels_)

    @staticmethod
    def encode_rgb(rgb_):
        """ encode R,G,B as 24-bit GRB word """
        return (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]
