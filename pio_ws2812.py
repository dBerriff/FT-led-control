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
    
    RGB_SHIFT = const(8)  # shift 24-bit colour to MSBytes
    
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
    """ extend PioWs2812 for NeoPixel strip """

    def __init__(self, pin, n_pixels):
        super().__init__(pin)
        self.n_pixels = n_pixels
        self.set_active(True)
        # for LED RGB values
        self.arr = array.array("I", [0]*n_pixels)

    def show(self, level):
        """ put pixel array into Tx FIFO, first setting level """
        arr = self.arr
        for i, c in enumerate(self.arr):
            r = int(((c >> 8) & 0xFF) * level)
            g = int(((c >> 16) & 0xFF) * level)
            b = int((c & 0xFF) * level)
            arr[i] = (g << 16) + (r << 8) + b
        self.sm.put(arr, self.RGB_SHIFT)

    def show_rgb(self):
        """ put pixel array into StateMachine Tx FIFO """
        self.sm.put(self.arr, self.RGB_SHIFT)

    def set(self, i, colour):
        """ set pixel array RGB values in WS2812 order """
        self.arr[i] = (colour[1] << 16) + (colour[0] << 8) + colour[2]

    def fill_all(self, colour):
        """ fill all pixels with color RGB """
        for i in range(self.n_pixels):
            self.arr[i] = (colour[1] << 16) + (colour[0] << 8) + colour[2]


def colour_chase(pnp, colour, level, wait):
    for i in range(pnp.n_pixels):
        pnp.set(i, colour)
        time.sleep(wait)
        pnp.show(level)
    time.sleep(0.2)
 

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    if pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    pos -= 170
    return pos * 3, 0, 255 - pos * 3
 
 
def rainbow_cycle(pnp, level, wait):
    for j in range(255):
        for i in range(pnp.n_pixels):
            rc_index = (i * 256 // pnp.n_pixels) + j
            pnp.set(i, wheel(rc_index & 255))
        pnp.show(level)
        time.sleep(wait)


def time_set_strip(pnp_, rgb_):
    """ coro: test and time fill-strip method """
    c_time = time.ticks_us()
    pnp_.fill_all(rgb_)
    print(f'Time to fill: {time.ticks_diff(time.ticks_us(), c_time):,}us')
    c_time = time.ticks_us()
    pnp_.show_rgb()
    print(f'Time to write: {time.ticks_diff(time.ticks_us(), c_time):,}us')


def main():
    """ """
    black = (0, 0, 0)
    red = (255, 0, 0)
    yellow = (255, 150, 0)
    green = (0, 255, 0)
    cyan = (0, 255, 255)
    blue = (0, 0, 255)
    purple = (180, 0, 255)
    white = (255, 255, 255)
    colors = (black, red, yellow, green, cyan, blue, purple, white)

    # configure the WS2812 LEDs
    num_leds = 64
    pin_num = 27
    level = 0.2

    # instantiate the PIO-driven NeoPixels
    p_np = Ws2812Strip(pin_num, num_leds)
    
    print('timed fill')
    time_set_strip(p_np, red)
    time.sleep(0.2)

    print("fills")
    for color in colors:
        p_np.fill_all(color)
        p_np.show(level)
        time.sleep(0.2)

    print("chases")
    for color in colors:
        colour_chase(p_np, color, level, 0.01)

    print("rainbow")
    rainbow_cycle(p_np, level, 0)

    p_np.fill_all(black)
    p_np.show(0)
    time.sleep(0.2)


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
