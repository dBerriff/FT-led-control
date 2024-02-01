# led.py
""" (r, g, b) functions """


def get_rgb_l(rgb_, level_):
    """ return level-converted rgb value """
    level_ = max(level_, 0)
    level_ = min(level_, 255)
    return (rgb_[0] * level_ // 255,
            rgb_[1] * level_ // 255,
            rgb_[2] * level_ // 255)


def get_rgb_gamma(gamma=2.6):
    """ return gamma correction tuple """
    return tuple(
            [round(pow(x / 255, gamma) * 255) for x in range(0, 256)])


def get_rgb_g_c(rgb_, rgb_gamma_):
    """ return gamma-corrected rgb value """
    return (rgb_gamma_[rgb_[0]],
            rgb_gamma_[rgb_[1]],
            rgb_gamma_[rgb_[2]])


def get_rgb_l_g_c(rgb_, level_, rgb_gamma_):
    """ return level-converted, gamma-corrected rgb value """
    level_ = max(level_, 0)
    level_ = min(level_, 255)
    return (rgb_gamma_[rgb_[0] * level_ // 255],
            rgb_gamma_[rgb_[1] * level_ // 255],
            rgb_gamma_[rgb_[2] * level_ // 255])
