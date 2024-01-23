# led_test.py

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
        self.gamma = gamma  # 2.6: Adafruit suggested value
        self.rgb_gamma = self.get_rgb_gamma_tuple(self.gamma)
        self.c_r_dim = self.Coord(self.n_cols, self.n_rows)
        self.coord_index = self.get_coord_index_dict()

    def get_coord_index_dict(self):
        """ correct grid addressing scheme
            - columns across, rows down
        """
        pixel_dict = {}
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                # reverse odd rows
                if col % 2:
                    r = self.n_rows - row - 1
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

    async def step_through_grid(self, rgb_):
        """ step through all pixels in index sequence """
        p_coord = self.Coord(0, 0)
        for _ in range(self.n_pixels):
            index = self.coord_index[p_coord]
            self[index] = rgb_
            self.write()
            await asyncio.sleep_ms(200)
            self[index] = self.OFF
            self.write()
            p_coord = self.coord_inc(p_coord)
    
    async def step_through_indices(self, rgb_):
        """ step through all pixels in index sequence """
        for index in range(self.n_pixels):
            self[index] = rgb_
            self.write()
            await asyncio.sleep_ms(200)
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

    def fill_diag(self, rgb, reverse=False):
        """ fill row with rgb value"""
        if reverse:
            col_max = self.n_cols - 1
            for col in range(self.n_cols):
                r_col = col_max - col
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
    colours = npg.Colours
    # level defines brightness with respect to 255 peak
    level = 68
    rgb = npg.get_rgb_l_g_c(colours['cyan'], level)

    # step forwards through all pixels
    await npg.step_through_indices(rgb)
    # step forwards through grid
    await npg.step_through_grid(rgb)

    # fill rows
    for row in range(npg.n_rows):
        npg.fill_row(row, rgb)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_row(row, npg.OFF)
        npg.write()
    # reverse row sequence; -2 to bounce straight back
    for row in range(npg.n_rows-2, -1, -1):
        npg.fill_row(row, rgb)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_row(row, npg.OFF)
        npg.write()

    # fill columns
    for col in range(npg.n_cols):
        npg.fill_col(col, rgb)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_col(col, npg.OFF)
        npg.write()
    # reverse sequence: -2 to bounce straight back
    for col in range(npg.n_cols-2, -1, -1):
        npg.fill_col(col, rgb)
        npg.write()
        await asyncio.sleep_ms(200)
        npg.fill_col(col, npg.OFF)
        npg.write()

    # fill diagonal
    npg.fill_diag(rgb)
    npg.write()
    await asyncio.sleep_ms(200)
    npg.fill_diag(npg.OFF)
    npg.write()
    # fill reverse diagonal
    npg.fill_diag(rgb, reverse=True)
    npg.write()
    await asyncio.sleep_ms(200)
    npg.fill_diag(npg.OFF, reverse=True)
    npg.write()
    # fill both diagonals
    npg.fill_diag(rgb)
    npg.fill_diag(rgb, reverse=True)
    npg.write()
    await asyncio.sleep_ms(1000)
    npg.fill_diag(npg.OFF)
    npg.fill_diag(npg.OFF, reverse=True)
    npg.write()
    await asyncio.sleep_ms(1000)
    
    # alternate diagonals
    for _ in range(8):
        npg.fill_diag(rgb)
        npg.write()
        await asyncio.sleep_ms(100)
        npg.fill_diag(npg.OFF)
        npg.write()
        npg.fill_diag(rgb, reverse=True)
        npg.write()
        await asyncio.sleep_ms(100)
        npg.fill_diag(npg.OFF, reverse=True)
        npg.write()
    await asyncio.sleep_ms(2)  # ensure final write() propagates


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
