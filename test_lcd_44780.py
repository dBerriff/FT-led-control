import machine
from machine import Pin, I2C
from lcd_44780 import LcdApi
from time import sleep

I2C_ADDR = 0x27
BLANK_LINE = " " * 16
rows = 2
columns = 16
lcd = LcdApi(scl=Pin(3), sda=Pin(2), f=10000, rows=rows, cols=columns)

lcd.put_str("I2C LCD Tutorial")
sleep(2)
lcd.clear()
lcd.write_line(0, "Count 0...10")
sleep(2)
for i in range(11):
    lcd.write_line(1, str(i))
    sleep(1)
    lcd.write_line(1, BLANK_LINE)
lcd.clear()
