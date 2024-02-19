# railway.py
""" model railway related classes """


class ColourSignal:
    """
        model railway colour signals
        - level_ is required
    """

    # change keys to match layout terminology

    def __init__(self, nps_, cs_, pixel_, level_):
        self.nps = nps_
        self.pixel = pixel_
        self.c_red = cs_.get_rgb('red', level_)
        self.c_yellow = cs_.get_rgb('yellow', level_)
        self.c_green = cs_.get_rgb('green', level_)
        self.c_off = (0, 0, 0)


class FourAspect(ColourSignal):
    """ model UK 4-aspect colour signal
        - bottom to top: red-yellow-green-yellow
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

    # (r, y, g, y)
    settings = {
        0: (1, 0, 0, 0),
        1: (0, 1, 0, 0),
        2: (0, 1, 0, 1),
        3: (0, 0, 1, 0)
    }

    def __init__(self, nps_, cs_, pixel_, level_):
        super().__init__(nps_, cs_, pixel_, level_)
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
        self.nps[self.i_red] = self.c_red if setting[0] == 1 else self.c_off
        self.nps[self.i_yw1] = self.c_yellow if setting[1] == 1 or setting[3] else self.c_off
        self.nps[self.i_grn] = self.c_green if setting[2] == 1 else self.c_off
        self.nps[self.i_yw2] = self.c_yellow if setting[3] == 1 else self.c_off
        self.nps.write()

    def set_by_blocks_clear(self, clr_blocks):
        """ set aspect by clear blocks """
        clr_blocks = min(clr_blocks, 3)  # > 3 clear is still 'green'
        self.set_aspect(clr_blocks)
