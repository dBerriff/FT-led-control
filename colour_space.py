# rgb.py
""" RGB grb_ data and functions """

from micropython import const


class ColourSpace:
    """ 
        implement 24-bit, 3-element tuple (R, G, B)
        - gamma-correction is explicitly applied by a lookup list
        - methods are all class methods
        - get_rgb_lg(), get_rgb_l(), get_rgb_g():
            -- suffix denotes transform(s): l: level,  g: gamma
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
    # faster than list comprehension
    RGB_GAMMA = []
    for x in range(256):
        RGB_GAMMA.append(round(pow(x / 255, GAMMA) * 255))
    RGB_GAMMA = tuple(RGB_GAMMA)

    @classmethod
    def get_rgb_lg(cls, rgb_, level_=255):
        """
            return a level-converted, gamma-corrected rgb value
            - rgb_template is colours dict key: str;
                or (r, g, b) as 8-bit int
        """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0, 0, 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return (
            cls.RGB_GAMMA[rgb_[0] * level_ // 255],
            cls.RGB_GAMMA[rgb_[1] * level_ // 255],
            cls.RGB_GAMMA[rgb_[2] * level_ // 255]
            )

    @classmethod
    def get_rgb_g(cls, rgb_):
        """ return a gamma-corrected rgb value """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0, 0, 0
        return (
            cls.RGB_GAMMA[rgb_[0]],
            cls.RGB_GAMMA[rgb_[1]],
            cls.RGB_GAMMA[rgb_[2]]
            )

    @classmethod
    def get_rgb_l(cls, rgb_, level_=255):
        """ return a level-converted rgb value """
        if isinstance(rgb_, str):
            try:
                rgb_ = cls.colours[rgb_]
            except KeyError:
                return 0, 0, 0
        level_ = max(level_, 0)
        level_ = min(level_, 255)
        return (
            rgb_[0] * level_ // 255,
            rgb_[1] * level_ // 255,
            rgb_[2] * level_ // 255
            )

    @classmethod
    def get_hsv_rgb(cls, h_, s_, v_):
        """
            see:
            https://github.com/python/cpython/blob/3.12/Lib/colorsys.py
            inputs: float [0.0...1.0]; calling method must check for range
            h_: hue, s_: saturation, v_: value
            returns:  r, g, b: int [0...255]
            - intermediate calculations are eliminated in this version
        """
        v_8 = v_ * 255.0  # 8-bit final value
        if s_ == 0.0:
            v_8_int = int(v_8)
            return v_8_int, v_8_int, v_8_int

        # keep i in range(6)
        if h_ == 1.0:
            h_ = 0.0
        h_6 = h_ * 6.0  # 6 colour sectors
        i = int(h_6)
        f = h_6 - i
        # select colour sector
        if i == 0:
            r = v_8
            g = v_8 * (1.0 - s_ * (1.0 - f))
            b = v_8 * (1.0 - s_)
        elif i == 1:
            r = v_8 * (1.0 - s_ * f)
            g = v_8
            b = v_8 * (1.0 - s_)
        elif i == 2:
            r = v_8 * (1.0 - s_)
            g = v_8
            b = v_8 * (1.0 - s_ * (1.0 - f))
        elif i == 3:
            r = v_8 * (1.0 - s_)
            g = v_8 * (1.0 - s_ * f)
            b = v_8
        elif i == 4:
            r = v_8 * (1.0 - s_ * (1.0 - f))
            g = v_8 * (1.0 - s_)
            b = v_8
        else:  # i == 5:
            r = v_8 
            g = v_8 * (1.0 - s_)
            b = v_8 * (1.0 - s_ * f)
        return int(r), int(g), int(b)
