from machine import Pin
from neopixel import NeoPixel
from time import sleep

# 0x19 is 25, approx 10% of 255, 0xff
WHT = (0x19, 0x19, 0x19)
RED = (0x19, 0x00, 0x00)
GRN = (0x00, 0x19, 0x00)
BLU = (0x00, 0x00, 0x19)
CYN = (0x00, 0x19, 0x19)
MGT = (0x19, 0x00, 0x19)
YEL = (0x19, 0x19, 0x00)
OFF = (0x00, 0x00, 0x00)

colours = (WHT, RED, GRN, BLU, CYN, MGT, YEL)
pin = Pin(28, Pin.OUT)   # GPIO28 as NeoPixel output
np = NeoPixel(pin, 1)  # NeoPixel driver for 1 pixel

for colour in colours:
    np[0] = colour  # set the first pixel to colour
    np.write()  # write data to all pixels
    sleep(5)
np[0] = OFF
np.write()

