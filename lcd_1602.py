# lcd1602.py
""" Refactor of Waveshare class for LCD1602 I2C Module """

from machine import Pin, I2C
from micropython import const
from time import sleep, sleep_ms


class LcdApi:
    """ drive LCD1602 display """
    # not all constants are used
    I2C_ADDR = const(62)  # I2C Address

    CLR_DISP = const(0x01)
    ENTRY_MODE = const(0x04)
    DISP_CONTROL = const(0x08)
    FN_SET = const(0x20)

    # flags for display entry mode
    ENT_LEFT = const(0x02)
    ENT_SHIFT_DEC = const(0x00)

    # flags for display on/off control
    DISP_ON = const(0x04)
    CURS_OFF = const(0x00)
    BLINK_OFF = const(0x00)

    # flags for function set
    MODE_4BIT = const(0x00)
    LINES_2 = const(0x08)
    LINES_1 = const(0x00)
    DOTS_5x8 = const(0x00)

    def __init__(self, sda, scl, cols=16, rows=2):
        i = 0 if sda in {0, 4, 8, 12, 16, 20} else 1
        self.i2c = I2C(i, sda=Pin(sda), scl=Pin(scl), freq=400_000)
        self._col = cols
        self._row = rows
        self._show_fn = self.MODE_4BIT | self.LINES_1 | self.DOTS_5x8
        self.active = False
        try:
            # self.address info only; ADDRESS used in code
            self.address = self.i2c.scan()[0]
            self.active = True
            print(f'I2C address: {self.address}')
        except IndexError:
            print('I2C address not found: print mode instead.')
        if self.active:
            self.start(rows)
        self._n_lines = None
        self._curr_line = None
        self._show_ctrl = None
        self._show_mode = None

    def command(self, cmd):
        """ invoke command """
        self.i2c.writeto_mem(self.I2C_ADDR, 0x80, chr(cmd))

    def set_cursor(self, col, row):
        """ set cursor for write """
        col |= 0x80 if row == 0 else 0xc0
        self.i2c.writeto(self.I2C_ADDR, bytearray([0x80, col]))

    def write(self, data):
        """ write out character at cursor position """
        self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(data))

    def write_out(self, arg):
        """ write out bytearray at cursor position """
        for b in bytearray(str(arg), 'utf-8'):
            self.i2c.writeto_mem(self.I2C_ADDR, 0x40, chr(b))

    def display(self):
        """ set display state (on) """
        self._show_ctrl |= self.DISP_ON
        self.command(self.DISP_CONTROL | self._show_ctrl)

    def start(self, lines):
        """ start routine as per Waveshare docs """
        self._n_lines = lines
        self._curr_line = 0
        self._show_fn |= self.LINES_2 if lines > 1 else self.LINES_1
        sleep_ms(50)

        # Send function set command 3 times (!)
        for _ in range(3):
            self.command(self.FN_SET | self._show_fn)
            sleep_ms(5)  # wait more than 4.1ms
        # turn the display on, cursor and blinking off
        self._show_ctrl = self.DISP_ON | self.CURS_OFF | self.BLINK_OFF
        self.display()
        self.clear()
        # Initialize to L > R text direction
        self._show_mode = self.ENT_LEFT | self.ENT_SHIFT_DEC
        self.command(self.ENTRY_MODE | self._show_mode)

    # interface functions

    def clear(self):
        if self.active:
            self.command(self.CLR_DISP)
            sleep_ms(2)

    def write_line(self, row, text):
        """ write text to display rows """
        if self.active:
            self.set_cursor(0, row)
            self.write_out(text)
        else:
            print(f'{row}: {text}')


def main():
    lcd = LcdApi(scl=21, sda=20)
    if not lcd.active:
        return
    print('lcd active')

    blank_line = " " * 16
    lcd.clear()
    lcd.write_line(0, "I2C LCD Tutorial")
    sleep(2)
    lcd.write_line(0, blank_line)
    lcd.write_line(0, "Count 0...10")
    sleep(2)
    for i in range(11):
        lcd.write_line(1, str(i))
        sleep(1)
        lcd.write_line(1, blank_line)
    lcd.clear()


if __name__ == '__main__':
    try:
        main()
    finally:
        print('Execution complete')
