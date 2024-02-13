# neo_pixel_helper.py
"""
    helper funcions for PixelStrip class
    - for development: move into class by alias when tested?
    - assignments such as: nps_[i] = nps_[1 - 1] are supported
"""

import asyncio
from random import randrange
from neo_pixel import PixelStrip



async def np_arc_weld(nps_, pixel_):
    """ coro: single pixel:
        simulate arc-weld flash and decay
    """
    arc_rgb_ = 'white'
    glow_rgb_ = 'red'
    for _ in range(2):
        for _ in range(randrange(100, 200)):
            level = randrange(127, 256)
            nps_[pixel_] = nps_.get_rgb(arc_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(20)
        for level in range(160, -1, -1):
            nps_[pixel_] = nps_.get_rgb(glow_rgb_, level)
            nps_.write()
            await asyncio.sleep_ms(10)
        await asyncio.sleep_ms(randrange(1_000, 5_000))


async def np_twinkler(nps_, pixel_):
    """ coro: single pixel:
        simulate gas-lamp twinkle
    """
    lamp_rgb = (0xff, 0xcf, 0x9f)
    base_level = 64
    dim_level = 95
    n_smooth = 3
    # levels list: take mean value
    levels = [0] * n_smooth
    l_index = 0
    for _ in range(100):
        twinkle = randrange(64, 128, 8)
        # randrange > 0; no 'pop'
        if randrange(0, 50) > 0:  # most likely
            levels[l_index] = base_level + twinkle
            level = sum(levels) // n_smooth
        # randrange == 0; 'pop'
        else:
            # set 'pop' across levels list
            for i in range(n_smooth):
                levels[i] = dim_level
            level = dim_level
        nps_[pixel_] = nps_.get_rgb(lamp_rgb, level)
        nps_.write()
        await asyncio.sleep_ms(randrange(20, 200, 20))
        l_index += 1
        l_index %= n_smooth

async def mono_chase(nps_, rgb_list, pause=20):
    """ np strip:
        fill count_ pixels with list of rgb values
        - n_rgb does not have to equal count_
    """
    n_pixels = nps_.n
    n_colours = len(rgb_list)
    index = 0
    for _ in range(1000):
        for i in range(n_colours):
            nps_[(index + i) % n_pixels] = rgb_list[i]
        nps_.write()
        await asyncio.sleep_ms(pause)
        nps_[index] = (0, 0, 0)
        index = (index + 1) % n_pixels

async def colour_chase(nps_, rgb_list, pause=20):
    """ np strip:
        fill count_ pixels with list of rgb values
        - n_rgb does not have to equal count_
    """
    n_pixels = nps_.n
    n_colours = len(rgb_list)
    c_index = 0
    for _ in range(1000):
        for i in range(n_pixels):
            nps_[i] = rgb_list[(i + c_index) % n_colours]
        nps_.write()
        await asyncio.sleep_ms(pause)
        c_index = (c_index - 1) % n_colours

class FourAspect:
    """
        model four-aspect railway colour signal
        - colour order, bottom to top: red-yellow-green-yellow
        - level_ is required
    """

    # change keys to match layout terminology
    aspect_codes = {
        'stop': 0,
        'caution': 1,
        'p_caution': 2,
        'clear': 3
        }

    # (r, y, g, y)
    settings = {
        0: (1, 0, 0, 0),
        1: (0, 1, 0, 0),
        2: (0, 1, 0, 1),
        3: (0, 0, 1, 0)
        }

    def __init__(self, nps_, pixel_, level_):
        self.nps = nps_
        self.pixel = pixel_
        self.c_red = nps_.get_rgb('red', level_)
        self.c_yellow = nps_.get_rgb('yellow', level_)
        self.c_green = nps_.get_rgb('green', level_)
        self.c_off = (0, 0, 0)
        self.i_red = pixel_
        self.i_yw1 = pixel_ + 1
        self.i_grn = pixel_ + 2
        self.i_yw2 = pixel_ + 3
        self.set_aspect('stop')

    def set_aspect(self, aspect, flash=False):
        """
            set signal aspect by number or code:
            0 - red
            1 - single yellow
            2 - double yellow
            3 - green
        """
        if isinstance(aspect, str):
            aspect = self.aspect_codes[aspect]
        setting = settings[aspect]
        nps_[pixel_] = self.c_red if setting[0] else self.c_off
        nps_[pixel_ + 1] = self.c_yellow if setting[1] else self.c_off
        nps_[pixel_ + 2] = self.c_green if setting[2] else self.c_off
        nps_[pixel_ + 3] = self.c_yellow if setting[0] else self.c_off
