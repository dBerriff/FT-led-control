"""
    Control WS2812E/NeoPixel lighting

    Thanks to MERG member Paul Redhead for information on PIO.

    Classes:

    PioWs2812
    Set pixel output for WS2812 LEDs (NeoPixels) by PIO state machine
    - there should be a 50µs pause between strip writes: not usually a problem
    
    Ws2812Strip(PioWs2812)
    This extends the PioWs2812 class by adding attributes and methods intended to
    match the NeoPixel interface, and to simplify user coding.
    See 'helper' functions for application-specific code.

    Notes:
    - methods do not implicitly write() pixels to allow for overlays
    - namedtuple RGB values are handled transparently

"""

import rp2
from machine import Pin
import array
from micropython import const


class PioWs2812:
    """
        Implement WS2812 driver using RP2040 programmable i/o
        See:
        - R Pi Pico C SDK: section 3.2.2
        - R Pi [Micro]Python SDK: section 3.9.2
        - https://tutoduino.fr/en/pio-rp2040-en/
            for simplified PIO code
    """

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
        f_ = 5_000_000  # this version
        self.pin = pin  # for trace/debug
        self.sm = rp2.StateMachine(0, PioWs2812.ws2812,  freq=f_,
                                   set_base=Pin(pin), out_base=Pin(pin))

    def set_active(self, state_):
        """ set StateMachine active-_state, True or False """
        self.sm.active(state_)


class Ws2812Strip(PioWs2812):
    """ extend PioWs2812 for NeoPixel strip
        - MicroPython NeoPixel interface is matched as per MP documentation
        - RGBW (bpp) not currently implemented
        - __setitem__, set_pixel() and set_strip() implicitly set GRB colour order
        - some code is repeated to avoid additional method calls
    """

    RGB_SHIFT = const(8)  # shift 24-bit colour to MSBytes in 32-bit word
    # RGBW_SHIFT = const(0)  # future use

    def __init__(self, pin, n_pixels, bpp=3):
        super().__init__(pin)
        self.n_pixels = n_pixels
        self.bpp = bpp  # 3 is RGB, 4 is RGBW; currently ignored
        self.n = n_pixels  # undocumented MP library attribute
        self.set_active(True)
        # array element type 'I': 32-bit unsigned integer
        self.arr = array.array('I', [0]*n_pixels)

    def __len__(self):
        """ matches NeoPixel interface """
        return self.n_pixels

    def __setitem__(self, index, colour):
        """ matches NeoPixel interface; RGB -> GRB """
        # RGB -> GRB for WS2812 order; shift to MSB on put()
        self.arr[index] = (colour[1] << 16) + (colour[0] << 8) + colour[2]

    def __getitem__(self, index):
        """ matches NeoPixel interface; GRB -> RGB """
        grb = self.arr[index]
        return (grb >> 8) & 0xff, (grb >> 16) & 0xff, grb & 0xff,

    def write(self):
        """ 'put' pixel array into StateMachine Tx FIFO """
        # shift moves rgb bits to MSB position
        self.sm.put(self.arr, self.RGB_SHIFT)

    def set_pixel(self, i, rgb_):
        """ set pixel RGB; duplicates __setitem__() """
        self.arr[i] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    def fill_array(self, rgb_):
        """ fill array with RGB """
        arr = self.arr  # avoid repeated dict lookup
        for i in range(self.n_pixels):
            arr[i] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    def set_range(self, index_, count_, rgb_):
        """ fill count_ pixels with rgb_  """
        arr = self.arr
        for _ in range(count_):
            index_ %= self.n
            arr[index_] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]
            index_ += 1

    def set_list(self, index_list_, rgb_):
        """ fill index_list pixels with rgb_ """
        arr = self.arr
        for i in index_list_:
            arr[i] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    def clear(self):
        """ clear all pixels """
        arr = self.arr
        for i in range(self.n_pixels):
            arr[i] = 0
