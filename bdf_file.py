# bdf_file.py
"""
    parse DBF file and build font pixel lists for 8x8 grid
    - can be run as CPython or MicroPython script
    - if run as CPython:
        file charset.json must be transferred to the Pico
    - sample fonts taken from:
        https://github.com/arduino-libraries/ArduinoGraphics/tree/master/extras

    N.B. minimal error checking in this version; appropriate font file structure is assumed
"""

import json
import array  # for explicit element type (I: unsigned int)


def get_font_bitmaps(filename):
    """
        read BDF file and return char bitmaps as dict:
            key: char, value: list of bitmaps by row
        - restricted to range of ASCII values
    """

    def get_tokens(f_):
        """ """
        line_ = f_.readline()
        line_.strip()
        return line_.split()

    preamble_dict = {'filename': filename}
    font_dict = {}
    with open(filename) as f:
        parse_preamble = True
        while parse_preamble:
            # TODO: count line reads to help spot malformed file
            line = f.readline()
            line.strip()
            if line.startswith('FONTBOUNDINGBOX'):
                tokens = line.split()
                font_width = int(tokens[1])
                font_height = int(tokens[2])
                preamble_dict['width'] = font_width
                preamble_dict['height'] = font_height
                parse_preamble = False

        parse_fonts = True
        while parse_fonts:
            line = f.readline()
            line.strip()
            if line.startswith('STARTCHAR'):
                for _ in range(5):  # 5 x parameter lines
                    tokens = get_tokens(f)
                    if tokens[0] == 'ENCODING':
                        code = int(tokens[1])
                    elif tokens[0] == 'BITMAP':
                        bit_map = array.array('I')
                        for _ in range(font_height):
                            tokens = get_tokens(f)
                            row = int(tokens[0], 16)
                            bit_map.append(row)
                        font_dict[code] = bit_map
                    if code >= 126:
                        parse_fonts = False
    return preamble_dict, font_dict


def get_8x8_char_indices(char_grid, col_offset, row_offset):
    """
        convert char (col, row) coords to strip indices
        - bdf fonts store byte arrays by row
        - grid is wired in snake order
        - explicit value comparisons for clarity
    """
    i_list = []
    for row in range(8):
        # process next byte array
        ba = char_grid[row]
        for col in range(8):
            # ls bit is left-most col
            # select bit and test result
            if ba & (1 << (7 - col)) != 0:
                c = col + col_offset
                r = row + row_offset
                if c % 2 == 1:  # odd row
                    r_index = 7 - r
                else:
                    r_index = r
                i_list.append(c * 8 + r_index)
    return i_list


def main():

    # !!! select required character set
    charset = '5x7'
    # !!!

    font_parameters, bitmaps = get_font_bitmaps(charset + '.bdf')
    print(font_parameters['filename'])
    w = font_parameters['width']
    h = font_parameters['height']
    # remove null character
    if 0 in bitmaps:
        bitmaps.pop(0)
    # TODO: fix padding
    top_rows = 1
    for code in bitmaps:
        # pad out to 8 rows
        for _ in range(top_rows):
            bitmaps[code].insert(0, 0)

    char_indices = {}
    for code in bitmaps:
        char_indices[chr(code)] = get_8x8_char_indices(bitmaps[code], 2, 0)
    # del bitmaps

    # write indices file
    with open(charset + '.json', 'w') as f:
        json.dump(char_indices, f)

    # confirm successful write of indices file
    with open(charset + '.json', 'r') as f:
        retrieved = json.load(f)
    print()
    for key in retrieved:
        print(f'"{key}": {retrieved[key]}')


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
