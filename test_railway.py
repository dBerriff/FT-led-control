# test_4_aspect.py

import asyncio
import time
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace
from railway import ThreeAspect, FourAspect


async def set_4_aspect(nps_, pixel_, level_, delay):
    """ """
    f_aspect = FourAspect(nps_, pixel_, level_)
    print(f_aspect)
    for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
        print(f'at pixel: {pixel_}; blocks clear: {bc}')
        f_aspect.set_by_blocks_clear(bc)
        await asyncio.sleep_ms(delay)
    await asyncio.sleep_ms(2_000)
    

async def set_3_aspect(nps_, pixel_, level_, delay):
    """ """
    f_aspect = ThreeAspect(nps_, pixel_, level_)
    for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
        print(f'at pixel: {pixel_}; blocks clear: {bc}')
        f_aspect.set_by_blocks_clear(bc)
        await asyncio.sleep_ms(delay)
    await asyncio.sleep_ms(2_000)
    

async def main():
    """ coro: test NeoPixel strip helper functions """

    pin_number = 15
    n_pixels = 30
    nps = Ws2812Strip(pin_number, n_pixels)
    cs = ColourSpace()

    asyncio.create_task(set_4_aspect(nps, 0, 128, 4_000))
    await set_3_aspect(nps, 8, 128, 5_000)
    
    nps.clear_strip()
    nps.write()
    await asyncio.sleep_ms(2000)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
