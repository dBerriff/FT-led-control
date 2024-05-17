# lcd_null.py
""" Base class for LCD values and methods """


class Lcd:
    """ LCD base class """
    # output defaults to print

    def __init__(self):
        self.active = False
        self._n_lines = None
        self._curr_line = None
        self._show_ctrl = None
        self._show_mode = None

    # interface functions

    def clear(self):
        pass

    def write_line(self, row, text):
        """ write text to display rows """
        if self.active:
            pass
        else:
            print(f'{row}: {text}')
