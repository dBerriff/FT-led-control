# test_np_grid.py

""" test LED- and NeoPixel-related classes
    - 'block' is an 8x8 square in the grid
    - 'grid' is the whole grid including any virtual blocks
"""

import asyncio
from np_grid_ws import BlockGrid
from colour_space import ColourSpace


async def main():
    """ coro: test np_grid methods  """

    pin_number = 27
    cs = ColourSpace()
    npg = BlockGrid(
        pin_number, n_cols_=16, n_rows_=8, charset_file='5x7.json')
    level = 64
    rgb = cs.get_rgb('dark_orange', level)

    print('display strings')
    await npg.display_string('MERG', rgb)
    npg.clear()

    await asyncio.sleep_ms(1000)
    # test character shift-left

    await npg.display_string_shift(' This is a test.', rgb)
    await asyncio.sleep_ms(1000)
    npg.clear()
    npg.write()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
