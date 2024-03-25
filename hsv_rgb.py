"""
    from Pimoroni examples and library
    - also, see: http://www.easyrgb.com/en/math.php
"""


def set_hsv(h_, s_, v_):
    """
        derived from Pimoroni GitHub code
        h_: hue: int, angle in degrees
        s_: saturation: float, 0 to 1
        v_: value: float, 0 to 1
    """

    h_ = (h_ % 360) / 360  # mod 360 ensures case_i in range(6)
    case_i = int(h_ * 6.0)
    f = h_ * 6.0 - case_i

    v_ *= 255.0
    p = v_ * (1.0 - s_)
    # q = v_ * (1.0 - f * s_)
    # t = v_ * (1.0 - (1.0 - f) * s_)

    if case_i == 0:
        r = v_
        g = v_ * (1.0 - (1.0 - f) * s_)
        b = p
    elif case_i == 1:
        r = v_ * (1.0 - f * s_)
        g = v_
        b = p
    elif case_i == 2:
        r = p
        g = v_
        b = v_ * (1.0 - (1.0 - f) * s_)
    elif case_i == 3:
        r = p
        g = v_ * (1.0 - f * s_)
        b = v_
    elif case_i == 4:
        r = v_ * (1.0 - (1.0 - f) * s_)
        g = p
        b = v_
    else:  # case_i == 5:
        r = v_
        g = p
        b = v_ * (1.0 - f * s_)

    return int(r), int(g), int(b)


for h in range(0, 361, 10):
    print(h)
    print(set_hsv(h, 0.5, 0.5))
