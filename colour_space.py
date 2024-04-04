# rgb.py
""" RGB values and methods """

from micropython import const


class ColourSpace:
    """ 
        values and methods return 3 x 8-bit RGB tuple
        - gamma-correction is set from a lookup list
        - methods are all class methods
        - _lg, _l, _g:
            -- suffix denotes: l: level,  g: gamma
        -
    """

    # commonly used RGB colour "templates"
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
    GAMMA = const(2.6)  # Adafruit value - see GitHub
    RGB_GAMMA = []  # list comprehension is slower
    for x in range(256):
        RGB_GAMMA.append(round(pow(x / 255, GAMMA) * 255))
    RGB_GAMMA = tuple(RGB_GAMMA)

    @classmethod
    def rgb_lg(cls, rgb_, level_=255):
        """ return RGB, level and gamma corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        r = cls.RGB_GAMMA[rgb_[0] * level_ // 255]
        g = cls.RGB_GAMMA[rgb_[1] * level_ // 255]
        b = cls.RGB_GAMMA[rgb_[2] * level_ // 255]
        return r, g, b

    @classmethod
    def rgb_l(cls, rgb_, level_=255):
        """ return RGB, level corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        r = rgb_[0] * level_ // 255
        g = rgb_[1] * level_ // 255
        b = rgb_[2] * level_ // 255
        return r, g, b

    @classmethod
    def rgb_g(cls, rgb_):
        """ return RGB, gamma corrected """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0
        r = cls.RGB_GAMMA[rgb_[0]]
        g = cls.RGB_GAMMA[rgb_[1]]
        b = cls.RGB_GAMMA[rgb_[2]]
        return r, g, b

    @staticmethod
    def hsv_rgb(hsv_):
        """
            input: HSV: 3 x float [0.0...1.0]
            return: RGB
        """
        h, s = hsv_[0], hsv_[1]
        v_u8 = hsv_[2] * 255
        if s == 0.0:
            v = int(v_u8)
            return v, v, v

        # keep i in range(6)
        if h == 1.0:
            h = 0.0
        h_6 = h * 6.0  # 6 colour sectors
        i = int(h_6)
        f = h_6 - i
        # select colour sector
        if i == 0:
            r = v_u8
            g = v_u8 * (1.0 - s * (1.0 - f))
            b = v_u8 * (1.0 - s)
        elif i == 1:
            r = v_u8 * (1.0 - s * f)
            g = v_u8
            b = v_u8 * (1.0 - s)
        elif i == 2:
            r = v_u8 * (1.0 - s)
            g = v_u8
            b = v_u8 * (1.0 - s * (1.0 - f))
        elif i == 3:
            r = v_u8 * (1.0 - s)
            g = v_u8 * (1.0 - s * f)
            b = v_u8
        elif i == 4:
            r = v_u8 * (1.0 - s * (1.0 - f))
            g = v_u8 * (1.0 - s)
            b = v_u8
        else:  # i == 5:
            r = v_u8
            g = v_u8 * (1.0 - s)
            b = v_u8 * (1.0 - s * f)

        return int(r), int(g), int(b)
