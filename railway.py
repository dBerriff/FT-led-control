# railway.py
""" model-railway related classes """

from collections import namedtuple
import asyncio
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace

Lights = namedtuple('Lights', ('r', 'y1', 'g', 'y2'))


class ColourSignal:
    """
        model railway grb_ signals
        - level_ is required
    """

    aspect_codes = {
        'stop': 0,
        'danger': 0,
        'red': 0,
        'caution': 1,
        'yellow': 1,
        'single yellow': 1,
        'preliminary caution': 2,
        'double yellow': 2,
        'clear': 3,
        'green': 3
    }
    # change keys to match layout terminology

    def __init__(self, nps_, pixel_, level_):
        self.nps = nps_
        self.pixel = pixel_
        self.cs = ColourSpace()
        self.clrs = {'red': self.cs.get_rgb_lg('red', level_),
                     'yellow': self.cs.get_rgb_lg('yellow', level_),
                     'green': self.cs.get_rgb_lg('green', level_),
                     'off': (0, 0, 0)
                     }
        

class FourAspect(ColourSignal):
    """ model UK 4-aspect grb_ signal
        - bottom to top: red-yellow-green-yellow
    """

    # (r, y, g, y)
    settings = {
        0: Lights(1, 0, 0, 0),
        1: Lights(0, 1, 0, 0),
        2: Lights(0, 1, 0, 1),
        3: Lights(0, 0, 1, 0)
        }

    def __init__(self, nps_, pixel_, level_):
        super().__init__(nps_, pixel_, level_)
        self.i_red = pixel_
        self.i_yw1 = pixel_ + 1
        self.i_grn = pixel_ + 2
        self.i_yw2 = pixel_ + 3
        self.set_aspect('red')

    def set_aspect(self, aspect):
        """
            set signal aspect by number or code:
            0 - red
            1 - single yellow
            2 - double yellow
            3 - green
        """
        if isinstance(aspect, str):
            if aspect in self.aspect_codes:
                aspect = self.aspect_codes[aspect]
            else:
                aspect = self.aspect_codes['red']
        setting = self.settings[aspect]
        self.nps[self.i_red] = self.clrs['red'] if setting[0] else self.clrs['off']
        self.nps[self.i_yw1] = self.clrs['yellow'] if setting[1] or setting[3] else self.clrs['off']
        self.nps[self.i_grn] = self.clrs['green'] if setting[2] else self.clrs['off']
        self.nps[self.i_yw2] = self.clrs['yellow'] if setting[3] else self.clrs['off']
        self.nps.write()

    def set_by_blocks_clear(self, clr_blocks):
        """ set aspect by clear blocks """
        clr_blocks = min(clr_blocks, 3)  # > 3 clear is still 'green'
        self.set_aspect(clr_blocks)


class ThreeAspect(ColourSignal):
    """ model UK 3-aspect grb_ signal
        - bottom to top: red-yellow-green
    """

    # (r, y, g)
    settings = {
        0: Lights(1, 0, 0, 0),
        1: Lights(0, 1, 0, 0),
        2: Lights(0, 0, 1, 0),
        3: Lights(0, 0, 1, 0)
    }

    def __init__(self, nps_, pixel_, level_):
        super().__init__(nps_, pixel_, level_)
        self.i_red = pixel_
        self.i_yw1 = pixel_ + 1
        self.i_grn = pixel_ + 2
        self.set_aspect('red')

    def set_aspect(self, aspect):
        """
            set signal aspect by number or code:
            0 - red
            1 - single yellow
            2 -> 3
            3 - green
        """
        if isinstance(aspect, str):
            if aspect in self.aspect_codes:
                aspect = self.aspect_codes[aspect]
            else:
                aspect = self.aspect_codes['red']
        if aspect == 2:
            aspect = 3
        setting = self.settings[aspect]
        self.nps[self.i_red] = self.clrs['red'] if setting[0] else self.clrs['off']
        self.nps[self.i_yw1] = self.clrs['yellow'] if setting[1] else self.clrs['off']
        self.nps[self.i_grn] = self.clrs['green'] if setting[2] else self.clrs['off']
        self.nps.write()

    def set_by_blocks_clear(self, clr_blocks):
        """ set aspect by clear blocks """
        clr_blocks = min(clr_blocks, 2)  # > 2 clear is still 'green'
        self.set_aspect(clr_blocks)


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
    asyncio.create_task(set_4_aspect(nps, 0, 128, 5_000))
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
