# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from collections import namedtuple
from machine import Pin
from neo_pixel import PixelStrip
from char_set import charset_2_8x8 as charset


class PixelGrid(PixelStrip):
    """ extend NPStrip to support BTF-Lighting grid
        - grid is wired 'snake' style; coord_dict corrects
    """

    Coord = namedtuple('Coord', ['c', 'r'])

    def __init__(self, np_pin, n_cols, n_rows, gamma=2.6):
        self.n_pixels = n_cols * n_rows
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels, gamma)
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.max_col = n_cols - 1
        self.max_row = n_rows - 1
        self.c_r_dim = self.Coord(self.n_cols, self.n_rows)
        self.coord_index = self.get_coord_index_dict()
        self.charset = None

    def get_coord_index_dict(self):
        """ correct grid addressing scheme
            - columns across, rows down as for most computer display software
        """
        coord_index_dict = {}
        max_row = self.n_rows - 1
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                if col % 2:  # odd row
                    r = max_row - row
                else:
                    r = row
                coord_index_dict[col, row] = col * self.n_rows + r
        return coord_index_dict

    def coord_inc(self, coord):
        """ increment cell coordinate """
        c_ = coord.c + 1
        if c_ == self.c_r_dim.c:
            c_ = 0
            r_ = coord.r + 1
            if r_ == self.c_r_dim.r:
                r_ = 0
        else:
            r_ = coord.r
        return self.Coord(c_, r_)

    def coord_dec(self, coord):
        """ decrement cell coordinate """
        c_ = coord.c - 1
        if c_ == -1:
            c_ = self.c_r_dim.c - 1
            r_ = coord.r - 1
            if r_ == -1:
                r_ = self.c_r_dim.r - 1
        else:
            r_ = coord.r
        return self.Coord(c_, r_)

    def fill_row(self, row, rgb):
        """ fill row with rgb value"""
        for col in range(self.n_cols):
            index = self.coord_index[col, row]
            self[index] = rgb

    def fill_col(self, col, rgb):
        """ fill col with rgb value"""
        for row in range(self.n_rows):
            index = self.coord_index[col, row]
            self[index] = rgb

    def fill_diagonal(self, rgb, reverse=False):
        """ fill diagonal with rgb value"""
        if reverse:
            for col in range(self.n_cols):
                r_col = self.max_col - col
                row = col
                index = self.coord_index[r_col, row]
                self[index] = rgb
        else:
            for col in range(self.n_cols):
                row = col
                index = self.coord_index[col, row]
                self[index] = rgb

    def fill_grid(self, rgb):
        """ fill grid with rgb value"""
        for index in range(self.n_pixels):
            self[index] = rgb

    def display_char(self, char_, rgb_):
        """ display the current charset character """
        if char_ in self.charset:
            char_grid = self.charset[char_]
            for row in range(self.n_rows):
                for col in range(self.n_cols):
                    index = self.coord_index[col, row]
                    if char_grid[row][col]:
                        self[index] = rgb_
                    else:
                        self[index] = self.OFF
        else:
            self.fill_grid(self.OFF)
        self.write()

    async def display_string(self, str_, rgb_, pause=1000):
        """ cycle throught the letters in a string """
        for char_ in str_:
            self.display_char(char_, rgb_)
            await asyncio.sleep_ms(pause)

async def main():
    """ set NeoPixel values on grid """
    
    async def blank_pause():
        """ fill grid with (0, 0, 0) and pause 1s """
        npg.fill_grid(npg.OFF)
        npg.write()
        await asyncio.sleep_ms(200)

    pin_number = 27
    npg = PixelGrid(pin_number, 8, 8)
    vis_colours = npg.Colours
    vis_colours.pop('black')
    colour_list = list(vis_colours.keys())
    colour_list.sort()
    colour_list = tuple(colour_list)
    print(f'colour list: {colour_list}')
    # level defines brightness with respect to 255 peak
    level = 64
    npg.charset = charset
    await blank_pause()
    rgb = npg.get_rgb_l_g_c(vis_colours['aqua'], level)

    chars = list(npg.charset.keys())
    chars.sort()
    for c in chars:
        npg.display_char(c, rgb)
        await asyncio.sleep_ms(1000)
    await blank_pause()

    
    for _ in range(2):
        await npg.display_string('MERG ', rgb)
        await asyncio.sleep_ms(1000)
    for _ in range(2):
        await npg.display_string('FAMOUS TRAINS DERBY ', rgb)
        await asyncio.sleep_ms(1000)

    npg.fill_grid(npg.OFF)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
