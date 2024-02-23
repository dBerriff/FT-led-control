"""
    Control WS2812E/NeoPixel lighting
    This software takes a basic approach to colour manipulation.
    For far more sophisticated approaches see:
    - Adafruit Circuit Python
    - FastLED project.

    Raspberry Pi documentation is the main source of information for the PIO
    implementation, and thanks to MERG member Paul Redhead for addition inspiration.
    Adafruit documentation is acknowledged as the main source of information on
    NeoPixels, with additional content from the FasLED project.
    See as an initial document:
    https://cdn-learn.adafruit.com/downloads/pdf/adafruit-neopixel-uberguide.pdf

    Classes:

    PioWs2812
    Set pixel output for a strip for a strip of WS2812 LEDs (aka NeoPixels: Adafruit).
    An RP2040 PIO StateMachine is used to improve performance over NeoPixel class.

    Ws2812Strip(PioWs2812)
    This extends the PioWs2812 class by adding attributes and methods intended to
    simplify user coding.
    The interface largely matches the NeoPixel class interface.
    An important difference for performance is that there is direct access to
    the RGB array; this particularly helps with grid character shifts.

    - 'set_' functions do not write() pixels - this allows for colour overlays
    - implicit setting of output levels and gamma correction is not included
        as this is more efficiently implemented before calling these methods
        (see the ColourSpace class)
    
    See also:
    PixelGrid(PixelStrip)
    Set pixel output for a rectangular grid, viewed as 8x8 pixel blocks

    ColourSpace
    Define basic colours and adjust RGB values for level and gamma correction.

"""
# Example using PIO to drive a set of WS2812 LEDs.

import rp2
from machine import Pin
import array
from micropython import const
import time


class PioWs2812:
    """
        Implement WS2812 driver using RP2040 programmable i/o
        See: https://docs.micropython.org/en/latest/library/
                     rp2.StateMachine.html#rp2.StateMachine
    """
    
    @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW,
                 out_shiftdir=rp2.PIO.SHIFT_LEFT,
                 autopull=True, pull_thresh=24)
    def ws2812():
        t1m1 = 1
        t2m1 = 4
        t3m1 = 2
        wrap_target()
        label("bitloop")
        out(x, 1)               .side(0)    [t3m1]
        jmp(not_x, "do_zero")   .side(1)    [t1m1]
        jmp("bitloop")          .side(1)    [t2m1]
        label("do_zero")
        nop()                   .side(0)    [t2m1]
        wrap()

    def __init__(self, pin):
        self.sm = rp2.StateMachine(0, PioWs2812.ws2812,  freq=8_000_000, sideset_base=Pin(pin))

    def set_active(self, state_):
        """ set StateMachine active, True or False """
        self.sm.active(state_)


class Ws2812Strip(PioWs2812):
    """ extend PioWs2812 for NeoPixel strip
        - MicroPython NeoPixel interface is matched as per documentation
        - not all NeoPixel parameters are instantiated:
            -- frequency fixed at 800kHz
            -- RGBW (bpp) not currently implemented
        - StateMachine pulls 32-bit words for Tx FIFO
        - it is marginally quicker to shift 24-bit colour to MSB
            as a block with sm.put(value, shift=8)
        - WS2812 expects colour order: GRB
            __setitem__, set_pixel(), set_strip() set order
        - code is repeated to avoid additional method calls
        - implicit conversion of colour-keys to RGB has been removed
    """

    RGB_SHIFT = const(8)  # shift 24-bit colour to MSBytes

    def __init__(self, pin, n_pixels, bpp=3, timing=1):
        super().__init__(pin)
        self.n_pixels = n_pixels
        self.bpp = bpp  # 3 is RGB, 4 is RGBW; currently ignored
        self.timing = timing  # 1 is 800kHz, 0 is 400kHz; currently ignored
        self.n = n_pixels  # NeoPixel undocumented
        self.set_active(True)
        # LED RGB values, typecode 'I' is 32-bit unsigned integer
        self.arr = array.array('I', [0]*n_pixels)

    def __len__(self):
        """ NeoPixel interface """
        return self.n_pixels

    def __setitem__(self, index, colour):
        """ NeoPixel interface """
        # RGB -> GRB for WS2812 order; shift to MSB on put()
        self.arr[index] = (colour[1] << 16) + (colour[0] << 8) + colour[2]

    def __getitem__(self, index):
        """ NeoPixel interface """
        grb = self.arr[index]
        return (grb >> 8) & 0xff, (grb >> 16) & 0xff, grb & 0xff,

    def write_level(self, level):
        """ put pixel array into Tx FIFO, first setting level """
        arr = self.arr
        for i, c in enumerate(self.arr):
            r = int(((c >> 8) & 0xFF) * level)
            g = int(((c >> 16) & 0xFF) * level)
            b = int((c & 0xFF) * level)
            arr[i] = (g << 16) + (r << 8) + b
        self.sm.put(arr, self.RGB_SHIFT)

    def write(self):
        """ 'put' pixel array into StateMachine Tx FIFO """
        self.sm.put(self.arr, self.RGB_SHIFT)

    def set_pixel(self, i, rgb_):
        """ set pixel colour in WS2812 order
            - duplicates __setitem__()
        """
        self.arr[i] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    def set_strip(self, rgb_):
        """ fill strip with RGB in WS2812 order """
        for i in range(self.n_pixels):
            self.arr[i] = (rgb_[1] << 16) + (rgb_[0] << 8) + rgb_[2]

    def set_list_rgb(self, index_list_, rgb_):
        """ fill index_list pixels with rgb_ """
        for index in index_list_:
            self[index] = rgb_

    def clear(self):
        """ set and write all pixels to off """
        for index in range(self.n_pixels):
            self[index] = (0, 0, 0)
        self.write()
