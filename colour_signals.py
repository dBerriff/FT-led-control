# colour_signals.py
""" 3- and 4-aspect UK railway colour signals """

import asyncio


def encode_sig_colours(r_y_g, cs_, driver_, level_):
    """"""
    # encode signal colours for driver_
    r = driver_.encode_rgb(cs_.rgb_lg(r_y_g[0], level_))
    y = driver_.encode_rgb(cs_.rgb_lg(r_y_g[1], level_))
    g = driver_.encode_rgb(cs_.rgb_lg(r_y_g[2], level_))
    return {'red': r, 'yellow': y, 'green': g}


class ColourSignal:
    """ model railway pixel-strip colour signals
        abstract base class
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

    def set_aspect(self, aspect):
        """ for subclass methods """
        return

    def set_by_blocks_clear(self, n_blocks_clr):
        """ set aspect by number of blocks clear """
        self.set_aspect(n_blocks_clr)


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
            self.nps[self.base_pixel + i] = self.colours[i] if s_config[i] else 0
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
            self.nps[self.base_pixel + i] = self.colours[i] if s_config[i] else 0
        self.nps.write()


async def main():
    """ """
    return

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
