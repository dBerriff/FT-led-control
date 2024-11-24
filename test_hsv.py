# ltest_np.py

""" test LED- and NeoPixel-related classes """

import asyncio
from pixel_strip import PixelStrip
from colour_space import ColourSpace
from plasma import Plasma2350
from ws2812 import Ws2812


async def main():
    """ coro: test HSV method
        degrees
        000 - red
        060 - yellow
        120 - green
        180 - cyan
        240 - blue
        300 - magenta
    """

    n_pixels = 20
    # set board_ and strip chipset methods
    cs = ColourSpace()
    board = Plasma2350()
    driver = Ws2812(board.strip_pins['dat'])
    nps = PixelStrip(driver, n_pixels)

    nps.clear_strip()
    await asyncio.sleep_ms(200)
    
    h = 0.0
    s = 1.0
    v = 0.5

    for h_0 in range(0, 360, 6):
        for p in range(n_pixels):
            h += 6.0
            if h > 360.0:
                h = 0.0
            nps.set_pixel_rgb(p, cs.hsv_rgb((h, s, v)))
        nps.write()
        await asyncio.sleep_ms(200)
    nps.clear_strip()
    await asyncio.sleep_ms(200)        


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained phase
        print('execution complete')
