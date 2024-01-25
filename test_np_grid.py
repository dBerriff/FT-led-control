# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from collections import namedtuple
from machine import Pin
from neo_pixel import PixelStrip


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

    def get_coord_index_dict(self):
        """ correct grid addressing scheme
            - columns across, rows down as for most computer display software
        """
        pixel_dict = {}
        max_row = self.n_rows - 1
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                if col % 2:  # odd row
                    r = max_row - row
                else:
                    r = row
                pixel_dict[col, row] = col * self.n_rows + r
        return pixel_dict

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
        """ increment cell coordinate """
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
        """ fill row with rgb value"""
        for row in range(self.n_rows):
            index = self.coord_index[col, row]
            self[index] = rgb

    def fill_diagonal(self, rgb, reverse=False):
        """ fill row with rgb value"""
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
        """ fill row with rgb value"""
        for index in range(self.n_pixels):
            self[index] = rgb


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
    print(colour_list)
    # level defines brightness with respect to 255 peak
    level = 128

    for colour in vis_colours:
        print(colour)
        rgb_ref = vis_colours[colour]
        rgb = npg.get_rgb_l_g_c(rgb_ref, level)
        print(vis_colours[colour], level, rgb)

        # fill grid
        print('fill grid')
        npg.fill_grid(rgb)
        npg.write()
        await asyncio.sleep_ms(1000)
        # fade out
        fade_l = level
        while fade_l > 20:
            rgb_ = npg.get_rgb_l_g_c(rgb_ref, fade_l)
            npg.fill_grid(rgb_)
            npg.write()
            await asyncio.sleep_ms(0)
            fade_l -= 1
        await blank_pause()

        # step forwards through all pixels
        print('Step through pixels in index order')
        for index in range(npg.n_pixels):
            npg[index] = rgb
            npg.write()
            await asyncio.sleep_ms(20)
            npg[index] = npg.OFF
            npg.write()
        await blank_pause()
            
        rgb = npg.get_rgb_l_g_c(vis_colours[colour], level)
        print('Step through pixels in grid (column, row) order')
        p_coord = npg.Coord(0, 0)
        for step in range(npg.n_pixels):
            index = npg.coord_index[p_coord]
            npg[index] = rgb
            npg.write()
            await asyncio.sleep_ms(20)
            npg[index] = npg.OFF
            await asyncio.sleep_ms(20)
            p_coord = npg.coord_inc(p_coord)
        await blank_pause()

        # fill rows
        print('Fill rows in row order')
        for row in range(npg.n_rows):
            npg.fill_row(row, rgb)
            npg.write()
            await asyncio.sleep_ms(100)
            npg.fill_row(row, npg.OFF)
            npg.write()
        # reverse row sequence; max-1 to bounce straight back
        for row in range(npg.max_row-1, -1, -1):
            npg.fill_row(row, rgb)
            npg.write()
            await asyncio.sleep_ms(100)
            npg.fill_row(row, npg.OFF)
            npg.write()

        # fill columns
        print('Fill columns in column order')
        for col in range(npg.n_cols):
            npg.fill_col(col, rgb)
            npg.write()
            await asyncio.sleep_ms(100)
            npg.fill_col(col, npg.OFF)
            npg.write()
        # reverse sequence: -2 to bounce straight back
        for col in range(npg.max_col-1, -1, -1):
            npg.fill_col(col, rgb)
            npg.write()
            await asyncio.sleep_ms(100)
            npg.fill_col(col, npg.OFF)
            npg.write()
        await blank_pause()

        # fill diagonal
        print('Fill diagonals')
        npg.fill_diagonal(rgb)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_diagonal(npg.OFF)
        npg.write()
        # fill reverse diagonal
        npg.fill_diagonal(rgb, reverse=True)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_diagonal(npg.OFF, reverse=True)
        npg.write()
        # fill both diagonals
        npg.fill_diagonal(rgb)
        npg.fill_diagonal(rgb, reverse=True)
        npg.write()
        await asyncio.sleep_ms(1000)
        npg.fill_diagonal(npg.OFF)
        await blank_pause()

        # alternate diagonals
        print('Switch between both diagonals')
        for i in range(8):
            npg.fill_diagonal(rgb)
            npg.write()
            await asyncio.sleep_ms(50)
            npg.fill_diagonal(npg.OFF)
            npg.write()
            npg.fill_diagonal(rgb, reverse=True)
            npg.write()
            await asyncio.sleep_ms(50)
            npg.fill_diagonal(npg.OFF, reverse=True)
            npg.write()
        await blank_pause()

    # fade out
    colour = 'aqua'
    rgb_ = vis_colours[colour]
    while level > 0:
        # fill both diagonals
        rgb = npg.get_rgb_l_g_c(rgb_, level)
        npg.fill_diagonal(rgb)
        npg.fill_diagonal(rgb, reverse=True)
        npg.write()
        await asyncio.sleep_ms(20)
        level -= 2
    await blank_pause()
            

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
