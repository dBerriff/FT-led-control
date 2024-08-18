# test_4_aspect.py

import asyncio
from colour_space import ColourSpace
from plasma import Plasma2350 as DriverBoard
from ws2812 import Ws2812
from pixel_strip import PixelStrip
from colour_signals import ThreeAspect, FourAspect, encode_sig_colours


async def main():
    """ coro: test NeoPixel strip helper functions
        - ColourSignal classes do not include coros
    """
    
    async def signal_4_aspect(pixel):
        """ test 4-aspect signal """
        four_aspect = FourAspect(nps, pixel, sig_colours)
        print(four_aspect)
        for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
            print(f'pixel: {pixel}; blocks clear: {bc}')
            four_aspect.set_by_blocks_clear(bc)
            await asyncio.sleep_ms(5000)  # arbitrary
        nps.clear_strip()
        await asyncio.sleep_ms(1)

    async def signal_3_aspect(pixel):
        """ test 3-aspect signal """
        three_aspect = ThreeAspect(nps, pixel, sig_colours)
        print(three_aspect)
        for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
            print(f'pixel: {pixel}; blocks clear: {bc}')
            three_aspect.set_by_blocks_clear(bc)
            await asyncio.sleep_ms(5000)  # arbitrary
        nps.clear_strip()
        await asyncio.sleep_ms(1)

    n_pixels = 30
    cs = ColourSpace()
    board = DriverBoard()
    driver = Ws2812(board.strip_pins['dat'])
    nps = PixelStrip(driver, n_pixels)

    level = 128
    signal_ryg = ((255, 0, 0), (207, 191, 0), (0, 255, 0))
    sig_colours = encode_sig_colours(signal_ryg, cs, driver, level)

    asyncio.create_task(signal_4_aspect(0))
    asyncio.create_task(signal_3_aspect(5))
    
    await asyncio.sleep(60)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
