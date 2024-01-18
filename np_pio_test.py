# np_pio_test.py
from rp2 import StateMachine
from machine import Pin
from neo_pixel import NPStrip
import array
import time

""" from Raspberry Pi Pico Python SDK 3.9.2. WS2812 LED (NeoPixel)
    - alternative to using MicroPython neopixel library """

# Create the StateMachine with the ws2812 program, outputting on pin_number
pin_number = 28
n_leds = 8
brightness = 0.2


nps = NPStrip(pin_number, n_leds)
np_ws = nps.ws2812
sm = StateMachine(0, np_ws, freq=8_000_000, sideset_base=Pin(pin_number))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(True)

# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(n_leds)])

##########################################################################

""" from Pico Python SDK Appendix A / Adafruit 'essential' NeoPixel code """


def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(n_leds)])
    for i, c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g << 16) + (r << 8) + b
    sm.put(dimmer_ar, 8)
    time.sleep_ms(10)


def pixels_set(i, color_):
    ar[i] = (color_[1] << 16) + (color_[0] << 8) + color_[2]


def pixels_fill(color_):
    for i in range(len(ar)):
        pixels_set(i, color_)


def color_chase(color_, wait):
    for i in range(n_leds):
        pixels_set(i, color_)
        time.sleep(wait)
        pixels_show()
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
 
 
def rainbow_cycle(wait):
    for j in range(255):
        for i in range(n_leds):
            rc_index = (i * 256 // n_leds) + j
            pixels_set(i, wheel(rc_index & 255))
        pixels_show()
        time.sleep(wait)


print("fills")
for color in nps.COLOURS:       
    pixels_fill(color)
    pixels_show()
    time.sleep(0.2)

print("chases")
for color in nps.COLOURS:       
    color_chase(color, 0.01)

print("rainbow")
rainbow_cycle(0)


pixels_fill(nps.BLK)
pixels_show()
time.sleep(0.2)
