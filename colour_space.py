# rgb.py
""" RGB colour data and functions """

from micropython import const


class ColourSpace:
    """ Colour class applies (fixed) gamma correction
        - get_rgb must be called explicitly
    """
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

    GAMMA = const(2.6)
    RGB_GAMMA = tuple(
        [round(pow(x / 255, GAMMA) * 255) for x in range(0, 256)])

    @classmethod
    def get_rgb(cls, c_template, level_):
        """
            set level-converted, gamma-corrected rgb value
            - pass in c_template as colours dict key or (r, g, b)
        """
        if isinstance(c_template, str):
            if c_template in cls.colours:
                c_template = cls.colours[c_template]
            else:
                c_template = (0, 0, 0)
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return cls.RGB_GAMMA[c_template[0] * level_ // 255], \
            cls.RGB_GAMMA[c_template[1] * level_ // 255], \
            cls.RGB_GAMMA[c_template[2] * level_ // 255]

    @classmethod
    def get_rgb_list(cls, template_list, level_):
        """ set level-converted, gamma-corrected rgb tuple values """
        return tuple([cls.get_rgb(t, level_) for t in template_list])