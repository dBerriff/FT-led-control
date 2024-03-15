# bdf_file.py
"""
    parse BDF font file and build pixel-lists for 8x8 grid
    - can be run as CPython or MicroPython script
    - if run as CPython:
        file <charset-name>.json must be transferred to the Pico
    - sample fonts taken from:
        https://github.com/arduino-libraries/ArduinoGraphics/tree/master/extras

    N.B. minimal error checking in this version; appropriate font file structure is assumed
    but certain keywords are checked for their presence.
"""

import json
import array  # for explicit element type (I: unsigned int)


def get_font_bitmaps(filename):
    """
        read BDF file and return char bitmaps as dict:
            key: char, value: list of bitmaps by row
        - restricted to range of ASCII values
    """

    def get_line_as_tokens(f_):
        """ fetch a line and split into tokens on space """
        line_ = ''
        try:
            line_ = f_.readline()
            line_.strip()
        except EOFError:
            print(f'get_line_as_tokens(): font file {f_} is incomplete.')
        return line_.split()

    def find_keyword(f_, keyword):
        """ consumes lines up to and including keyword line
            - keyword line returned as tokens split on space
        """
        line_ = ''
        while not line_.startswith(keyword):
            try:
                line_ = f_.readline()
                line_.strip()
            except EOFError:
                print(f'find_keyword(): font file {f_} is incomplete.')
        return line_.split()

    preamble_dict = {'filename': filename}
    font_dict = {}
    # no exception handling!
    print(f'font filename: {filename}')
    with open(filename) as f:
        tokens = find_keyword(f, 'FONTBOUNDINGBOX')
        preamble_dict['width'] = int(tokens[1])
        font_height = int(tokens[2])
        preamble_dict['height'] = font_height
        # optional: consume remainder of preamble block
        find_keyword(f, 'ENDPROPERTIES')

        parse_fonts = True
        # check for end of file?
        while parse_fonts:
            find_keyword(f, 'STARTCHAR')
            tokens = find_keyword(f, 'ENCODING')
            code = int(tokens[1])
            # only scan ASCII set
            if code > 126:
                break  # end parsing
            find_keyword(f, 'BITMAP')
            bit_map = array.array('I')
            for _ in range(font_height):
                tokens = get_line_as_tokens(f)
                # encode hexadecimal characters as integer
                row = int(tokens[0], 16)  # hexadecimal data
                bit_map.append(row)
            font_dict[code] = bit_map
            # optional: consume remainder of character block
            find_keyword(f, 'ENDCHAR')
        font_dict.pop(0, 0)  # default value prevents error if not in dict

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
            # ms bit is left-most col
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

    # === select required character set (no file extension)

    charset = '4x6'

    # ===

    font_parameters, bitmaps = get_font_bitmaps(charset + '.bdf')
    
    """ 
    # for debug / logging; note: JSON converts int dict key to str
    with open(charset + '_bmap.json', 'w') as f:
        json.dump({x: list(bitmaps[x]) for x in list(bitmaps.keys())}, f)
    """

    # pad out bitmaps at top to 8 rows
    pad_rows = 8 - font_parameters['height']
    if pad_rows > 0:
        pad = array.array('I')
        for _ in range(pad_rows):
            pad.append(0)

        for key in bitmaps:
            bitmaps[key] = pad + bitmaps[key]
            print(key, bitmaps[key])

    char_indices = {}
    for key in bitmaps:
        char_indices[chr(key)] = get_8x8_char_indices(bitmaps[key], 2, 0)
    # del bitmaps

    # write indices file
    with open(charset + '.json', 'w') as f:
        json.dump(char_indices, f)

    # optional: confirm successful write of indices file
    with open(charset + '.json', 'r') as f:
        retrieved = json.load(f)
    print()
    print('Encoded characters:')
    for key in retrieved:
        print(f'"{key}": {retrieved[key]}')


if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
