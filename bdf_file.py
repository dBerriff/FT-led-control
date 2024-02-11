# bdf_file.py
"""
    parse DBF file and build font pixel lists for 8x8 grid
    - assumes grid is wired in snake (strip) order
    - can be run as CPython or MicroPython script
    - if run as CPython:
        file charset.json must be transferred to the Pico
    - padding might need adjusting for specific fonts
    - sample fonts taken from:
        https://github.com/arduino-libraries/ArduinoGraphics/tree/master/extras

    N.B. no error checking in this version; appropriate font file structure is assumed
"""

import json


def get_font_bitmaps(filename):
    """
        read BDF file and return char bitmaps as dict:
            key: char, value: list of bitmaps by row
        - restricted to range of ASCII values
    """

    def get_tokens(line_):
        """ """
        line_.strip()
        return line_.split()

    char_dict = {}
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
                parse_preamble = False
        pad_width = (8 - font_width + 1) // 2
        pad_height = 8 - font_height

        parse_fonts = True
        while parse_fonts:
            line = f.readline()
            line.strip()
            if line.startswith('STARTCHAR'):
                for _ in range(5):  # 5 x parameter lines
                    line = f.readline()
                    tokens = get_tokens(line)
                    if tokens[0] == 'ENCODING':
                        code = int(tokens[1])
                        if code == 0:
                            break  # exclude code 0
                    elif tokens[0] == 'BITMAP':
                        if pad_height:
                            bitmap = [0] * pad_height  # pad for 8 rows on grid
                        else:
                            bitmap = []
                        for _ in range(font_height):
                            line = f.readline()
                            tokens = get_tokens(line)
                            row = int(tokens[0], 16)
                            row = row >> pad_width  # pad to right
                            bitmap.append(row)
                        char_dict[chr(code)] = bitmap
                    if code >= 126:
                        parse_fonts = False
    return char_dict


def main():

    def get_8x8_char_indices(char_grid):
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
                    if col % 2 == 1:  # odd row
                        r_index = 7 - row
                    else:
                        r_index = row
                    i_list.append(col * 8 + r_index)
        return i_list

    # !!! select required character set
    charset_file = '5x7.bdf'
    # !!!
    print(charset_file)

    bitmaps = get_font_bitmaps(charset_file)
    print(bitmaps)

    char_indices = {}
    for ch in bitmaps:
        char_indices[ch] = get_8x8_char_indices(bitmaps[ch])

    for ch in char_indices:
        print(ch, char_indices[ch])

    with open('charset.json', 'w') as f:
        json.dump(char_indices, f)

    # confirm successful write (and read)
    with open('charset.json', 'r') as f:
        retrieved = json.load(f)
    for ch in retrieved:
        print(ch, retrieved[ch])


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
