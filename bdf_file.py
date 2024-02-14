# bdf_file.py
"""
    parse BDF font file and build pixel-lists for 8x8 grid
    - can be run as CPython or MicroPython script
    - if run as CPython:
        file <charset-name>.json must be transferred to the Pico
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
        """ split lines by space into tokens """
        line_ = f_.readline()
        line_.strip()
        return line_.split()

    def find_keyword(f_, keyword):
        """ helps skip unused line
            - consumes lines up to and including keyword line
        """
        line_ = f_.readline()
        line_.strip()
        while not line_.startswith(keyword):
            line_ = f_.readline()
            line_.strip()

    preamble_dict = {'filename': filename}
    font_dict = {}
    with open(filename) as f:
        parse_preamble = True
        while parse_preamble:
            line = f.readline()
            line.strip()
            if line.startswith('FONTBOUNDINGBOX'):
                tokens = line.split()
                preamble_dict['width'] = int(tokens[1])
                font_height = int(tokens[2])
                preamble_dict['height'] = font_height
                # consume remainder of preamble block
                find_keyword(f, 'ENDPROPERTIES')
                break

        parse_fonts = True
        while parse_fonts:
            line = f.readline()
            line.strip()
            if line.startswith('STARTCHAR'):
                for _ in range(5):  # 5 x parameter lines
                    tokens = get_tokens(f)
                    if tokens[0] == 'ENCODING':
                        code = int(tokens[1])
                        if code > 126:
                            parse_fonts = False
                            break
                    elif tokens[0] == 'BITMAP':
                        bit_map = array.array('I')
                        for _ in range(font_height):
                            tokens = get_tokens(f)
                            row = int(tokens[0], 16)  # hexadecimal
                            bit_map.append(row)
                        font_dict[code] = bit_map
            # consume remainder of character block
            find_keyword(f, 'ENDCHAR')

    return preamble_dict, font_dict


def get_8x8_char_indices(char_grid, col_offset=0, row_offset=0):
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
            # select bit and test
            if ba & (1 << (7 - col)) > 0:
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
    # for debug / logging; JSON converts int dict key to str
    with open(charset + '_bmap.json', 'w') as f:
        json.dump({x: list(bitmaps[x]) for x in list(bitmaps.keys())}, f)

    # remove null character if in dict
    bitmaps.pop(0, 0)
    # pad out to 8 rows
    top_rows = 8 - font_parameters['height']
    if top_rows > 0:
        for key in bitmaps:
            for _ in range(top_rows):
                # pad with empty row in position 0
                bitmaps[key].insert(0, 0)

    char_indices = {}
    for key in bitmaps:
        char_indices[chr(key)] = get_8x8_char_indices(bitmaps[key], 2, 0)
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
