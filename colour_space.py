# rgb.py
""" RGB colour data and functions """

from micropython import const


class ColourSpace:
    """ 
        implements 8-bit RGB colours as 3-element tuples (R, G, B)
        each colour is represented by an integer in range(256), 0 to 255
        method get_rgb() applies brightness level and gamma correction
        brightness is in range(256)
        gamma-correction is applied from a look-up list to speed up processing
        methods are all @classmethod
        list comprehension not used for faster computation
    """

    # full brightness colour "templates"
    colours = {
        'amber': (255, 100, 0),
        'aqua': (50, 255, 255),
        'black': (0, 0, 0),
        'blue': (0, 0, 255),
        'cyan': (0, 255, 255),
        'ghost_white': (248, 248, 255),
        'gold': (255, 255, 30),
        'green': (0, 255, 0),
        'jade': (0, 255, 40),
        'magenta': (255, 0, 255),
        'mint_cream': (245, 255, 250),
        'old_lace': (253, 245, 230),
        'orange': (255, 165, 0),
        'dark_orange': (255, 140, 0),
        'pink': (242, 90, 255),
        'purple': (180, 0, 255),
        'red': (255, 0, 0),
        'snow': (255, 250, 250),
        'teal': (0, 255, 120),
        'white': (255, 255, 255),
        'yellow': (255, 255, 0)
    }

    # build gamma-correction lookup list
    GAMMA = const(2.6)
    RGB_GAMMA = []
    for x in range(0, 256):
        RGB_GAMMA.append(round(pow(x / 255, GAMMA) * 255))
    RGB_GAMMA = tuple(RGB_GAMMA)

    @classmethod
    def get_rgb(cls, rgb_template, level_=255):
        """
            return a level-converted, gamma-corrected rgb value
            - c_template is colours dict key: str, or (r, g, b)
            - explicit tests for level_ == 255 or 0 could be included
                if these values are frequently set
        """
        if isinstance(rgb_template, str):
            try:
                rgb_template = cls.colours[rgb_template]
            except KeyError:
                return 0, 0, 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return cls.RGB_GAMMA[rgb_template[0] * level_ // 255], \
            cls.RGB_GAMMA[rgb_template[1] * level_ // 255], \
            cls.RGB_GAMMA[rgb_template[2] * level_ // 255]

    @classmethod
    def get_rgb_list(cls, template_list, level_):
        """ return a tuple of level-converted, gamma-corrected rgb values """
        values = []
        for t in template_list:
            values.append(cls.get_rgb(t, level_))
        return tuple(values)
