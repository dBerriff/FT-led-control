# FT-led-control
Control LED lighting by Pi Pico PWM

Control serial pixel-strip lighting by PIO output

Developed for Famous Trains, Derby

Shared with MERG Raspberry Pi Special Interest Group

Scripts; .py files are written for the R Pi Pico except for parse_bdf.py:

5x7.bdf: 
- font definition file from Arduino GitHub repository

5x7.json: 
- font definition file for pixel-strip grid (8 x 8) (ASCII character set only)

buttons.py: 
- Handle button click or hold. Event triggered by release of button.
- click = 1; hold = 2; event == ‘A1’ means button ‘A’ has been clicked

colour_signals.py: 
- Three- or four-aspect colour signal modelling.

colour_space.py: 
- RGB and HSV colour-handling values and methods. Class methods and values only.
- RGB: each colour is in int range: 0 … 255 inclusive.
- HSV: each value is in float range: 0.0 … 1.0 inclusive, although 1.0 for H will set to 0.0
- H: will change to float range 0.0º … 359.9º as more intuitive.

lcd_1602.py: 
- Methods and values for sending output to a I2C LCD display. 2 rows of 16 characters.
- Derived from Waveshare code which was in turn derived from C code.

led_pwm.py: 
- Pulse-width modulation control of a single (conventional) LED.

parse_bdf.py: 
- Convert a font bdf file to a JSON file for pixel-strip grid characters.
- Will run on a desktop or the Pi Pico.

pixel_strip.py: 
- Core methods and values for setting a pixel strip.
Imports the methods and values for specific strip microcontrollers.

pixel_strip_helper.py: 
- Domain-specific methods for setting a pixel strip. Example: arc-welding effect.

plasma_2040.py: 
- Pimoroni Plasma 2040 board-specific method and values.
Supports on-board pin connections and the method for setting the on-board tri-colour LED.

state_transition.py: 
- The main application to set layout ambient lighting.

test scripts:
- test_colour_signals.py
- test_grid.py
- test_hsv.py
- test_led.py
- test_strip.py

v_time.py: 
- Methods and values to implement an independent time-of-day clock, usually sped up.
Speed increase is achieved by dividing the number of virtual milliseconds per actual second.

ws2812.py: 
- Pixel-strip microcontroller-specific methods and values.
