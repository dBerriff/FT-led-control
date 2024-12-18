# test_grid.py

""" test WS1802-related classes
    - test for 8x8 pixel grid
"""

import asyncio
from colour_space import ColourSpace
from plasma import Plasma2040, Plasma2350
from ws2812 import Ws2812
from pixel_strip import BlockGrid


async def main():
    """ coro: test WS1802 grid methods """
    grid_cols = 8
    grid_rows = 8
    blocks = 2

    cs = ColourSpace()
    board = Plasma2040()
    print(board.NAME)
    print(f'Processor f: {machine.freq():,}')
    board.set_onboard((0, 64, 0))
    driver = Ws2812(board.strip_pins['dat'])
    pg = BlockGrid(driver, grid_cols, grid_rows, blocks, '5x7.json')

    level = 64
    rgb = cs.rgb_lg('dark_orange', level)

    print('shift display strings')
    await pg.shift_string_rgb(' Pimoroni', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(1000)
    await pg.shift_string_rgb(' Plasma 2040 or 2350', rgb)
    pg.clear_strip()
    await asyncio.sleep_ms(500)
    board.set_onboard((0, 0, 0))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained phase
        print('Execution complete')
