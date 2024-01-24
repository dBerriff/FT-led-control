# test_np_grid.py

""" test LED- and NeoPixel-related classes """

import asyncio
from machine import Pin
from collections import namedtuple
from micropython import const
from neo_pixel import NPStrip


class NPGrid(NPStrip):
    """ extend NPStrip to support BTF-Lighting grid
        - grid is wired 'snake' style; coord_dict corrects
    """
    Coord = namedtuple('Coord', ['c', 'r'])
    OFF = const((0, 0, 0))

    def __init__(self, np_pin, n_cols, n_rows, gamma=2.6):
        self.n_pixels = n_cols * n_rows
        super().__init__(Pin(np_pin, Pin.OUT), self.n_pixels, gamma)
        self.np_pin = np_pin  # for logging/debug
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.max_col = n_cols - 1
        self.max_row = n_rows - 1
        self.gamma = gamma  # 2.6: Adafruit suggested value
        self.rgb_gamma = self.get_rgb_gamma_tuple(self.gamma)
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
                # odd rows: scan in reverse direction
                if col % 2:  # == 1
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

    async def step_through_indices(self, rgb_, pause_ms=20):
        """ step through all pixels in index sequence """
        for index in range(self.n_pixels):
            self[index] = rgb_
            self.write()
            await asyncio.sleep_ms(pause_ms)
            self[index] = self.OFF
            self.write()

    async def step_through_grid(self, rgb_, pause_ms=20):
        """ step through all pixels in index sequence """
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                index = self.coord_index[(c, r)]
                self[index] = rgb_
                self.write()
                await asyncio.sleep_ms(pause_ms)
                self[index] = self.OFF
                self.write()
    
        for c in range(self.n_cols):
            for r in range(self.n_rows):
                index = self.coord_index[(c, r)]
                self[index] = rgb_
                self.write()
                await asyncio.sleep_ms(pause_ms)
                self[index] = self.OFF
                self.write()

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


async def main():
    """ set NeoPixel values on grid """

    pin_number = 27
    npg = NPGrid(pin_number, 8, 8)
    vis_colours = npg.Colours
    vis_colours.pop('black')
    colour_list = list(vis_colours.keys())
    print(colour_list)
    # level defines brightness with respect to 255 peak
    level = 68

    for colour in vis_colours:
        print(colour)
        rgb = npg.get_rgb_l_g_c(vis_colours[colour], level)
        # step forwards through all pixels
        print('Step through pixels in index order')
        await npg.step_through_indices(rgb)
        print('Step through pixels in grid (column, row) order')
        await npg.step_through_grid(rgb)

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
        npg.fill_diagonal(npg.OFF, reverse=True)
        npg.write()
        await asyncio.sleep_ms(200)
        
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
            

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
