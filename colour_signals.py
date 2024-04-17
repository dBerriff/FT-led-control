# colour_signals.py
""" 3- and 4-aspect UK railway colour signals """

import asyncio
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812
from pixel_strip import PixelStrip


class ColourSignal:
    """ model railway pixel-strip colour signals
        - aspect-codes set by name or integer
        - simplistic block-occupancy model
    """

    aspect_codes = {
        'stop': 0, 'danger': 0, 'red': 0,
        'caution': 1, 'yellow': 1, 'single yellow': 1,
        'preliminary caution': 2, 'double yellow': 2,
        'clear': 3, 'green': 3
        }

    def __init__(self, nps_, base_pixel_, colours_):
        self.nps = nps_
        self.base_pixel = base_pixel_
        self.colours = colours_

    def aspect_as_int(self, aspect):
        """ return aspect as int """
        if isinstance(aspect, str):
            if aspect in self.aspect_codes:
                aspect = self.aspect_codes[aspect]
            else:
                aspect = self.aspect_codes['red']
        return int(aspect)

    def set_by_blocks_clear(self, blocks_clr):
        """ set aspect by n blocks clear """
        self.set_aspect(blocks_clr)


class FourAspect(ColourSignal):
    """ model UK 4-aspect colour signal
        - bottom to top: red-yellow-green-yellow
    """
    # (r, y, g, y)
    aspect_states = {
        0: (1, 0, 0, 0),
        1: (0, 1, 0, 0),
        2: (0, 1, 0, 1),
        3: (0, 0, 1, 0)
        }

    MAX_ASPECT = 3

    def __init__(self, nps_, pixel_, clrs_):
        super().__init__(nps_, pixel_, clrs_)
        self.colours = (
            clrs_['red'], clrs_['yellow'], clrs_['green'], clrs_['yellow'])
        self.set_aspect('red')

    def set_aspect(self, aspect):
        """ set signal aspect by aspect key or number """
        aspect = min(self.aspect_as_int(aspect), self.MAX_ASPECT)
        s_config = self.aspect_states[aspect]
        for i, state in enumerate(s_config):
            pixel = self.base_pixel + i
            p_state = s_config[i]
            self.nps[pixel] = self.colours[i] if p_state else 0
        self.nps.write()

class ThreeAspect(ColourSignal):
    """ model UK 3-aspect colour signal
        - bottom to top: red-yellow-green-yellow
    """
    # (r, y, g)
    aspect_states = {
        0: (1, 0, 0),
        1: (0, 1, 0),
        2: (0, 0, 1)
        }

    MAX_ASPECT = 2

    def __init__(self, nps_, pixel_, clrs_):
        super().__init__(nps_, pixel_, clrs_)
        self.colours = (
            clrs_['red'], clrs_['yellow'], clrs_['green'])
        self.set_aspect('red')

    def set_aspect(self, aspect):
        """ set signal aspect by aspect key or number """
        aspect = min(self.aspect_as_int(aspect), self.MAX_ASPECT)
        s_config = self.aspect_states[aspect]
        for i, state in enumerate(s_config):
            pixel = self.base_pixel + i
            p_state = s_config[i]
            self.nps[pixel] = self.colours[i] if p_state else 0
        self.nps.write()


async def main():
    """ coro: test NeoPixel strip helper functions
        - ColourSignal classes do not include coros
    """
    n_pixels = 30
    cs = ColourSpace()
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, n_pixels)

    level = 128
    # encode colours as 24-bit word
    red = driver.encode_rgb(cs.rgb_lg((255, 0, 0), level))
    yellow = driver.encode_rgb(cs.rgb_lg((255, 255, 0), level))
    green = driver.encode_rgb(cs.rgb_lg((0, 255, 0), level))
    colours = {'red': red, 'yellow': yellow, 'green': green}

    pixel = 0
    four_aspect = FourAspect(nps, pixel, colours)
    print(four_aspect)
    for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
        print(f'at pixel: {pixel}; blocks clear: {bc}')
        four_aspect.set_by_blocks_clear(bc)
        await asyncio.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(1000)

    pixel = 5
    three_aspect = ThreeAspect(nps, pixel, colours)
    print(three_aspect)
    for bc in [0, 1, 2, 3, 4, 3, 2, 1, 0]:
        print(f'at pixel: {pixel}; blocks clear: {bc}')
        three_aspect.set_by_blocks_clear(bc)
        await asyncio.sleep_ms(1000)
    nps.clear_strip()
    await asyncio.sleep_ms(500)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
