# rgb.py
""" RGB colour data and functions """

# from micropython import const


class ColourSpace:
    """ 
        implement 24-bit RGB colour: 3-element tuple (R, G, B)
        - gamma-correction is applied by a lookup list
        - methods are all class methods
        - get_rgb_lg(), get_rgb_l(), get_rgb_g():
            suffix denotes transform: level and or gamma
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
    GAMMA = 2.6  # Adafruit uses this value?
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
        """
            return a gamma-corrected rgb value """
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
            see: http://www.easyrgb.com/en/math.php
            h_: hue: int, angle in degrees
            s_: saturation: float, range 0 to 1
            v_: value: float, range 0 to 1
        """

        v_0 = v_ * 255.0

        if s_ == 0.0:
            v_0 = int(v_0)
            return v_0, v_0, v_0

        h = (h_ % 360) / 60  # case_i in range(6)
        case_i = int(h)
        f = h - case_i

        # intermediate variables to clarify formulae
        v_1 = int(v_0 * (1.0 - s_))
        v_2 = int(v_0 * (1.0 - s_ * f))
        v_3 = int(v_0 * (1.0 - s_ * (1.0 - f)))
        v_0 = int(v_0)

        if case_i == 0:
            rgb = v_0, v_3, v_1
        elif case_i == 1:
            rgb = v_2, v_0, v_1
        elif case_i == 2:
            rgb = v_1, v_0, v_3
        elif case_i == 3:
            rgb = v_1, v_2, v_0
        elif case_i == 4:
            rgb = v_3, v_1, v_0
        else:  # case_i == 5:
            rgb = v_0, v_1, v_2

        return rgb
