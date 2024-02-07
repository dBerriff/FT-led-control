# rgb.py
""" RGB colour data and functions """

from micropython import const

colours = {
        'amber': (255, 100, 0),
        'aqua': (50, 255, 255),
        'black': (0, 0, 0),
        'blue': (0, 0, 255),
        'cyan': (0, 255, 255),
        'gold': (255, 255, 30),
        'green': (0, 255, 0),
        'jade': (0, 255, 40),
        'magenta': (255, 0, 255),
        'old_lace': (253, 245, 230),
        'orange': (255, 165, 0),
        'dark_orange': (255, 140, 0),
        'pink': (242, 90, 255),
        'purple': (180, 0, 255),
        'red': (255, 0, 0),
        'teal': (0, 255, 120),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0)
        }


class Colour:
    """ Colour class applies (fixed) gamma correction
        - get_rgb must be called explicitly
    """

    gamma = const(2.6)
    rgb_gamma = tuple(
        [round(pow(x / 255, gamma) * 255) for x in range(0, 256)])

    def __init__(self, colour_):
        self._colour = colour_

    def get_rgb(self, level_):
        """ set level-converted, gamma-corrected rgb value """
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return self.rgb_gamma[self._colour[0] * level_ // 255], \
            self.rgb_gamma[self._colour[1] * level_ // 255], \
            self.rgb_gamma[self._colour[2] * level_ // 255]
