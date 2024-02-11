# byte_array.py
"""
    Stand-alone script:
    build 8x8 charset and save as a JSON file
    - char pixels saved as list indices,
        compensated for grid
    - run as CPython and upload charset.json,
        or run as MicroPython file
"""

import json


charset_1_8x8 = {
        'A': (
            0b00000000,
            0b00011000,
            0b00100100,
            0b00100100,
            0b00100100,
            0b00111100,
            0b00100100,
            0b00100100
        ),
        'B': (
            0b00000000,
            0b00111000,
            0b00100100,
            0b00100100,
            0b00111000,
            0b00100100,
            0b00100100,
            0b00111000
        )
}


def main():

    def get_8x8_char_indices(char_grid):
        """ return char coords """
        i_list = []
        for row in range(8):
            row_byte = char_grid[row]
            for col in range(8):
                pix = row_byte & (1 << (7 - col))
                if pix:
                    if col % 2 == 1:  # odd row
                        r_index = 7 - row
                    else:
                        r_index = row
                    i_list.append(col * 8 + r_index)
        return i_list

    # !!! select required character set
    charset = charset_1_8x8
    # !!!
    char_indices = {}
    for ch in charset_1_8x8:
        char_indices[ch] = get_8x8_char_indices(charset[ch])

    with open('charset.json', 'w') as f:
        json.dump(char_indices, f)

    # confirm succesful write (and read)
    with open('charset.json', 'r') as f:
        retrieved = json.load(f)
    for ch in retrieved:
        print(ch, retrieved[ch])

if __name__ == '__main__':
    try:
        main()
    finally:
        print('execution complete')
