""" HD44780 compatible character LCD """

from micropython import const
from machine import Pin, I2C
from time import sleep, sleep_ms


class LcdApi:
    """
        API for generic HD44780-compatible character LCDs
        - these devices typically have a seperate I2C I/O board
        - see: https://microcontrollerslab.com/
               i2c-lcd-esp32-esp8266-micropython-tutorial/#
    """

    # from avrlib lcd.h
    # HD44780 LCD controller command set

    CLR = const(0x01)  # DB0: clear display
    HOME = const(0x02)  # DB1: return to home position

    ENTRY_MODE = const(0x04)  # DB2: set entry mode
    ENTRY_INC = const(0x02)  # DB1: increment
    ENTRY_SHIFT = const(0x01)  # DB0: shift

    ON_CTRL = const(0x08)  # DB3: turn lcd/cursor on
    ON_DISPLAY = const(0x04)  # DB2: turn display on
    ON_CURSOR = const(0x02)  # DB1: turn cursor on
    ON_BLINK = const(0x01)  # DB0: blinking cursor

    MOVE = const(0x10)  # DB4: move cursor/display
    MOVE_DISP = const(0x08)  # DB3: move display (0-> move cursor)
    MOVE_RIGHT = const(0x04)  # DB2: move right (0-> left)

    FUNCTION = const(0x20)  # DB5: function set
    FUNCTION_8BIT = const(0x10)  # DB4: set 8BIT mode (0->4BIT mode)
    FUNCTION_2LINES = const(0x08)  # DB3: two lines (0->one line)
    FUNCTION_10DOTS = const(0x04)  # DB2: 5x10 font (0->5x7 font)
    FUNCTION_RESET = const(0x30)  # See "Initializing by Instruction" section

    CGRAM = const(0x40)  # DB6: set CG RAM address
    DDRAM = const(0x80)  # DB7: set DD RAM address

    RS_CMD = const(0)
    RS_DATA = const(1)

    RW_WRITE = const(0)
    RW_READ = const(1)

    # ===

    i2c_addr = const(39)  # I2C Address
    # PCF8574 pin definitions
    MASK_RS = const(0x01)  # P0
    MASK_RW = const(0x02)  # P1
    MASK_E = const(0x04)  # P2

    SHIFT_BACKLIGHT = const(3)  # P3
    SHIFT_DATA = const(4)  # P4-P7

    def __init__(self, sda, scl, cols=16, rows=2):
        i = 0 if sda in (0, 4, 8, 12, 16, 20) else 1
        self.i2c = I2C(i, sda=Pin(sda), scl=Pin(scl), freq=10_000)
        try:
            self.address = self.i2c.scan()[0]
            self.active = True
        except IndexError:
            self.active = False
            print('LCD display I2C address not found')
            return
        sleep_ms(20)  # Allow LCD time to powerup
        # Send reset 3 times
        for _ in range(3):
            self.write_nibble(self.FUNCTION_RESET)
            sleep_ms(5)  # Need to delay at least 4.1 msec
        # Put LCD into 4-bit mode
        self.write_nibble(self.FUNCTION)
        sleep_ms(1)

        # ===
        if rows > 4:
            rows = 4
        if cols > 40:
            cols = 40
        self.cursor_x = 0
        self.cursor_y = 0
        self.implied_newline = False
        self.backlight = True
        self.display_off()
        self.backlight_on()
        self.clear()
        self.write_command(self.ENTRY_MODE | self.ENTRY_INC)
        # self.hide_cursor()
        self.display_on()
        cmd = self.FUNCTION
        if rows == 2:
            cmd |= self.FUNCTION_2LINES
        self.write_command(cmd)
        self.num_rows = rows
        self.num_cols = cols

    def display_on(self):
        """ turn on display """
        self.write_command(self.ON_CTRL | self.ON_DISPLAY)

    def display_off(self):
        """ turn off display """
        self.write_command(self.ON_CTRL)

    def move_to(self, cursor_x, cursor_y):
        """ move cursor to (x, y) """
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40  # Lines 1 & 3 add 0x40
        if cursor_y & 2:  # Lines 2 & 3 add number of columns
            addr += self.num_cols
        self.write_command(self.DDRAM | addr)

    def put_char(self, char):
        """ write char and advance cursor """
        if char == '\n':
            if self.implied_newline:
                pass
            else:
                self.cursor_x = self.num_cols
        else:
            self.write_data(ord(char))
            self.cursor_x += 1
        if self.cursor_x >= self.num_cols:
            self.cursor_x = 0
            self.cursor_y += 1
            self.implied_newline = (char != '\n')
        if self.cursor_y >= self.num_rows:
            self.cursor_y = 0
        self.move_to(self.cursor_x, self.cursor_y)

    def put_str(self, string):
        """ write string """
        for char in string:
            self.put_char(char)

    def write_nibble(self, nibble):
        """ write nibble to the LCD """
        byte = ((nibble >> 4) & 0x0f) << self.SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

    def backlight_on(self):
        """ turn backlight on """
        self.i2c.writeto(self.i2c_addr, bytes([1 << self.SHIFT_BACKLIGHT]))

    def backlight_off(self):
        """ turn backlight off """
        self.i2c.writeto(self.i2c_addr, bytes([0]))

    def write_command(self, cmd):
        """ write a command """
        byte = ((self.backlight << self.SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = ((self.backlight << self.SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        if cmd <= 3:
            # home & clear commands require 4.1 ms delay
            sleep_ms(5)

    def write_data(self, data):
        """ write data """
        byte = (self.MASK_RS |
                (self.backlight << self.SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = (self.MASK_RS |
                (self.backlight << self.SHIFT_BACKLIGHT) |
                ((data & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

    # interface functions

    def clear(self):
        """ clear display """
        if self.active:
            self.write_command(self.CLR)
            self.write_command(self.HOME)
            self.cursor_x = 0
            self.cursor_y = 0

    def write_line(self, row, text):
        """ write text to display rows """
        if self.active:
            self.move_to(0, row)
            self.put_str(text)
        else:
            print(f'{row}: {text}')


def main():
    from dh_2040 import Dh2040

    board = Dh2040()
    lcd = LcdApi(sda=board.LCD_SDA, scl=board.LCD_SCL)
    if not lcd.active:
        return
    print('lcd active')

    blank_line = " " * 16
    lcd.clear()
    lcd.write_line(0, "  I2C LCD Test  ")
    sleep(2)
    lcd.write_line(0, blank_line)
    lcd.write_line(0, "Count 0-10")
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
        print('execution complete')
