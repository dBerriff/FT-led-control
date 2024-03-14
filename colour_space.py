# rgb.py
""" RGB colour data and functions """

from micropython import const
from collections import namedtuple

RGB = namedtuple ('RGB', ('r', 'g', 'b'))
 
class ColourSpace:
    """ 
        implement 24-bit RGB colour: 3-element tuple (R, G, B)
        - gamma-correction is applied by a lookup list
        - methods are all @classmethod
        - get_rgb_lg(), get_rgb_l(), get_rgb_g():
            suffix denotes transform: level and or gamma
    """

    # full brightness colour "templates"
    colours = {
        'amber': RGB(255, 100, 0),
        'aqua': RGB(50, 255, 255),
        'black': RGB(0, 0, 0),
        'blue': RGB(0, 0, 255),
        'cyan': RGB(0, 255, 255),
        'ghost_white': RGB(248, 248, 255),
        'gold': RGB(255, 255, 30),
        'green': RGB(0, 255, 0),
        'jade': RGB(0, 255, 40),
        'magenta': RGB(255, 0, 255),
        'mint_cream': RGB(245, 255, 250),
        'old_lace': RGB(253, 245, 230),
        'orange': RGB(255, 165, 0),
        'dark_orange': RGB(255, 140, 0),
        'pink': RGB(242, 90, 255),
        'purple': RGB(180, 0, 255),
        'red': RGB(255, 0, 0),
        'snow': RGB(255, 250, 250),
        'teal': RGB(0, 255, 120),
        'white': RGB(255, 255, 255),
        'yellow': RGB(255, 255, 0)
    }

    # build gamma-correction lookup list
    GAMMA = const(2.6)  # Adafruit uses this value?
    # faster than list comprehension
    RGB_GAMMA = []
    for x in range(0, 256):
        RGB_GAMMA.append(round(pow(x / 255, GAMMA) * 255))
    RGB_GAMMA = tuple(RGB_GAMMA)

    @classmethod
    def get_rgb_lg(cls, rgb_template, level_=255):
        """
            return a level-converted, gamma-corrected rgb value
            - rgb_template is colours dict key: str;
                or (r, g, b) as 8-bit int
        """
        if isinstance(rgb_template, str):
            try:
                rgb_template = cls.colours[rgb_template]
            except KeyError:
                return 0, 0, 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return RGB(
            r = cls.RGB_GAMMA[rgb_template.r * level_ // 255], \
            g = cls.RGB_GAMMA[rgb_template.g * level_ // 255], \
            b = cls.RGB_GAMMA[rgb_template.b * level_ // 255]
            )

    @classmethod
    def get_rgb_g(cls, rgb_template):
        """
            return a gamma-corrected rgb value """
        if isinstance(rgb_template, str):
            try:
                rgb_template = cls.colours[rgb_template]
            except KeyError:
                return 0, 0, 0
        return RGB(
            r = cls.RGB_GAMMA[rgb_template.r], \
            g = cls.RGB_GAMMA[rgb_template.g], \
            b = cls.RGB_GAMMA[rgb_template.b]
            )

    @classmethod
    def get_rgb_l(cls, rgb_template, level_=255):
        """ return a level-converted rgb value """
        if isinstance(rgb_template, str):
            try:
                rgb_template = cls.colours[rgb_template]
            except KeyError:
                return 0, 0, 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return RGB(
            r = rgb_template.r * level_ // 255, \
            g = rgb_template.g * level_ // 255, \
            b = rgb_template.b * level_ // 255
            )


def main():
    """ test ColourSpace class """
    c_space = ColourSpace()
    for c in c_space.colours:
        rgb = c_space.colours[c]
        print(f'{c}: {rgb} {c_space.get_rgb_g(rgb)}')

if __name__ == '__main__':
    main()