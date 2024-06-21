import machine
from machine import Pin, I2C
from lcd_1602 import LcdApi
from time import sleep

BLANK_LINE = " " * 16
rows = 2
columns = 16
lcd = LcdApi(scl=21, sda=20)

lcd.write_line(0, "I2C LCD Tutorial")
sleep(2)
lcd.clear()
lcd.write_line(0, "Count 0...10")
sleep(2)
for i in range(11):
    lcd.write_line(1, str(i))
    sleep(1)
    lcd.write_line(1, BLANK_LINE)
lcd.clear()
