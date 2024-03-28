"""
    Control WS2812E/NeoPixel lighting

    Thanks to MERG member Paul Redhead for information on PIO.

    Encoding:
    User is expected to work with (R, G, B) 8-bit values
    WS2812 pixel words are coded as 32-bit GRBW with W = 0
    W (white) byte is added by left-shift in PIO 'put'

    Classes:

    PioWs2812
    Set pixel output for WS2812 LEDs (NeoPixels) by PIO state machine
    - there should be a 50µs pause between strip writes: normal awaits exceed this
    
    Ws2812Strip(PioWs2812)
    This extends the PioWs2812 class by adding general application-related
    attributes and methods. Helper methods support specific use-cases.

    Notes:
    - set and encode methods do not write to pixels to allow for overlays
        -- write() must be called to display the output
"""

import rp2
from machine import Pin
import array
from micropython import const
from colour_space import ColourSpace


class PioWs2812:
    """
        Implement WS2812 driver using RP2040 programmable i/o
        See:
        - R Pi Pico C SDK: section 3.2.2
        - R Pi [Micro]Python SDK: section 3.9.2
        - https://tutoduino.fr/en/pio-rp2040-en/
            for simplified PIO code
    """

    GRBW_SHIFT = const(8)  # shift 24-bit GRB to MSBytes in 32-bit word

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
        - __setitem__, set_pixel() and set_strip() implicitly set GRB grb_ order
        - some code is repeated to avoid additional method calls
    """

    def __init__(self, pin, n_pixels, bpp=3):
        super().__init__(pin)
        self.n_pixels = n_pixels
        self.bpp = bpp  # 3 is RGB, 4 is RGBW; currently ignored
        self.cs = ColourSpace()
        self.n = n_pixels  # undocumented MP library attribute
        self.set_active(True)
        # typecode: 'I': 32-bit unsigned integer
        self.arr = array.array('I', [0]*n_pixels)

    def __len__(self):
        """ number of pixels """
        return self.n_pixels

    def __setitem__(self, index, grb_):
        """ set 24-bit GRB """
        self.arr[index] = grb_

    def __getitem__(self, index):
        """ return 24-bit GRB """
        return self.arr[index]

    def write(self):
        """ 'put' GRB array into StateMachine Tx FIFO """
        # shift moves rgb bits to MSB position
        self.sm.put(self.arr, self.GRBW_SHIFT)

    def set_pixel(self, index, grb_):
        """ set pixel RGB; duplicates __setitem__() """
        self.arr[index] = grb_

    def set_strip(self, grb_):
        """ fill pixel strip with GRB """
        arr = self.arr  # avoid repeated dict lookup
        for i in range(self.n_pixels):
            arr[i] = grb_

    def set_range(self, index_, count_, grb_):
        """ fill count_ pixels with GRB  """
        arr = self.arr
        for _ in range(count_):
            arr[index_] = grb_
            index_ += 1
            if index_ == self.n_pixels:
                index_ = 0

    def set_list(self, index_list_, grb_):
        """ fill index_list pixels with GRB """
        arr = self.arr
        for i in index_list_:
            arr[i] = grb_

    def clear_strip(self):
        """ set all pixels to 0 """
        arr = self.arr
        for i in range(self.n_pixels):
            arr[i] = 0

    def set_pixel_rgb(self, index, colour):
        """ set pixel RGB; duplicates __setitem__() """
        self.arr[index] = self.encode(colour)

    def set_strip_rgb(self, rgb_):
        """ fill pixel strip with RGB """
        arr = self.arr
        grb = self.encode(rgb_)
        for i in range(self.n_pixels):
            arr[i] = grb

    def set_range_rgb(self, index_, count_, rgb_):
        """ fill count_ pixels with RGB  """
        self.set_range(index_, count_, self.encode(rgb_))

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with RGB """
        self.set_list(index_list_, self.encode(rgb_))

    @staticmethod
    def encode(rgb_):
        """ encode rgb as single 24-bit GRB word """
        return (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    @staticmethod
    def decode(grb_):
        """ decode GRB word to RGB tuple """
        return (grb_ >> 8) & 0xff, (grb_ >> 16) & 0xff, grb_ & 0xff

    # alternative GRB direct encoding

    def encode_lg(self, rgb_, level_=255):
        """ encode rgb as 24-bit GRB word, level and gamma corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = self.cs.colours[rgb_]
            except KeyError:
                return 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        r = self.cs.RGB_GAMMA[rgb_[0] * level_ // 255]
        g = self.cs.RGB_GAMMA[rgb_[1] * level_ // 255]
        b = self.cs.RGB_GAMMA[rgb_[2] * level_ // 255]
        return (g << 16) + (r << 8) + b

    def encode_g(self, rgb_):
        """ encode rgb as 24-bit GRB word, gamma corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = self.cs.colours[rgb_]
            except KeyError:
                return 0
        r = self.cs.RGB_GAMMA[rgb_[0]]
        g = self.cs.RGB_GAMMA[rgb_[1]]
        b = self.cs.RGB_GAMMA[rgb_[2]]
        return (g << 16) + (r << 8) + b

    def encode_l(self, rgb_, level_):
        """ encode rgb as 24-bit GRB word, level corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = self.cs.colours[rgb_]
            except KeyError:
                return 0
        r = rgb_[0] * level_ // 255
        g = rgb_[1] * level_ // 255
        b = rgb_[2] * level_ // 255
        return (g << 16) + (r << 8) + b
