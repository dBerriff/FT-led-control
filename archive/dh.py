# dh.py
"""
    Set LED strip using Pimoroni library
    written for Pimoroni Plasma 2040 p_2040
    
    Non-asyncio version
    Gamma correction implicit in the Pimoroni software. 
    
    Script runs until powered off or Reset button pressed
    - note: LED strip will retain phase until powered off
    - set phase to 'off' before stopping the script
    
    Three buttons are used: A, B and User (labelled BOOT)
    (RESET will stop the current script and run main.py, if present)
    - buttons have 2 states: 0: open; 1: pressed
    The system has 3 states:

    - 'off': all LEDs off; this is the start phase.
        always returns system to 'off' phase (does not stop code)

    - 'day': day/night illumination; A-button sets and toggles day/night

    - 'fade': fade from day to night and back repeatedly; B-button sets

    - time.ticks_ms() is used to measure short intervals
        time.time() is used for multiple-seconds intervals:
        (returns the number of seconds elapsed since the Epoch)

    - print() statements confirm action: many or all of these can be deleted
    - elif statements with pass are "no action" statements included to show structure
"""

import plasma
from plasma import plasma2040
import time
from pimoroni import RGBLED, Button, Analog

# ====== parameters
 
NUM_LEDS = 30

# light levels
day_rgb = (90, 80, 45)
night_rgb = (10, 30, 80)
off_rgb = (0, 0, 0)
# fade timings
fade_ms = 200  # ms/percent change - increase for slower fade
day_hold_s = 15  # s
night_hold_s = 5  # s

# ====== end-of-parameters


def set_strip(rgb_):
    """ set whole strip to rgb value """
    for i in range(NUM_LEDS):
        led_strip.set_rgb_u8(i, rgb_[0], rgb_[1], rgb_[2])


def set_strip_level(rgb_, level):
    """
        set whole strip to adjusted level
        - level in range 0 - 255
    """
    r = rgb_[0] * level // 255
    g = rgb_[1] * level // 255
    b = rgb_[2] * level // 255
    set_strip((r, g, b))


def get_fade_rgb(rgb_0, rgb_1, percent):
    """
        return the current fade rgb value
        - inefficient but tests the concept
    """
    r = rgb_0[0] + (rgb_1[0] - rgb_0[0]) * percent // 100
    g = rgb_0[1] + (rgb_1[1] - rgb_0[1]) * percent // 100
    b = rgb_0[2] + (rgb_1[2] - rgb_0[2]) * percent // 100
    return r, g, b


led = RGBLED(plasma2040.LED_R, plasma2040.LED_G, plasma2040.LED_B)
led.set_rgb_u8(128, 0, 0)  # onboard red: power on, LED strip off
 
button_a = Button(plasma2040.BUTTON_A)
button_b = Button(plasma2040.BUTTON_B)
button_u = Button(plasma2040.USER_SW)
 
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma2040.DAT)
sense = Analog(plasma2040.CURRENT_SENSE, plasma2040.ADC_GAIN, plasma2040.SHUNT_RESISTOR)

strip_rgb = off_rgb
set_strip(strip_rgb)
sys_state = 'off'
print('In phase "off"')
day_night_state = 'day'  # default?

fade_deltas = (0, 0, 0)
fade_count = 0
fade_rgb = strip_rgb
fade_state = 'down'
t_fade_0 = time.ticks_ms()
fade_percent = 0
prev_fade = 'down'
hold_interval_s = day_hold_s
hold_start_ms = time.ticks_ms()

led_strip.start()
count = 0
t_last_ms = time.ticks_ms()


while True:
    # clear button states then poll for press event
    btn_a_state = 0
    btn_b_state = 0
    btn_u_state = 0
    # if a button is set, following buttons are skipped
    if button_a.read():
        btn_a_state = 1
    elif button_b.read():
        btn_b_state = 1
    elif button_u.read():
        btn_u_state = 1

    # if event then possibly change system phase
    # fade change of phase is handled separately
    if any((btn_a_state, btn_b_state, btn_u_state)):
        print()
        print(f'button: a: {btn_a_state}, b: {btn_b_state}, u: {btn_u_state}')
        print(f'State: {sys_state}')
        if sys_state == 'off':
            if btn_a_state:
                print('Set phase "day"')
                strip_rgb = day_rgb
                sys_state = 'day'
                day_night_state = 'day'
                led.set_rgb_u8(0, 64, 0)  # onboard green for this phase
            elif btn_b_state:
                print('Set phase "fade"')
                strip_rgb = day_rgb
                sys_state = 'fade'
                fade_state = 'down'
                fade_percent = 0
                fade_rgb = strip_rgb
                led.set_rgb_u8(0, 0, 64)  # onboard blue for this phase
                t_fade_0 = time.ticks_ms()
            elif btn_u_state:
                pass
            set_strip(strip_rgb)

        elif sys_state == 'day':
            if btn_a_state:
                # toggle between day and night
                if day_night_state == 'day':
                    print('Set night')
                    strip_rgb = night_rgb
                    day_night_state = 'night'
                else:
                    print('Set day')
                    strip_rgb = day_rgb
                    day_night_state = 'day'
            elif btn_b_state:
                pass
            elif btn_u_state:
                print('Set phase "off"')
                day_night_state = 'day'
                strip_rgb = off_rgb
                sys_state = 'off'
                led.set_rgb_u8(128, 0, 0)
            set_strip(strip_rgb)

        elif sys_state == 'fade':
            if btn_a_state:
                pass
            elif btn_b_state:
                pass
            elif btn_u_state:
                print('Set phase "off"')
                day_night_state = 'day'
                strip_rgb = off_rgb
                sys_state = 'off'
                led.set_rgb_u8(128, 0, 0)
            set_strip(strip_rgb)

    if sys_state == 'fade':
        # fade LED level in simple percentage steps
        # fade from rgb_0 -> rgb_1
        # 100% fade means rgb_1 is set
        # simple algorithm to test concept; code is repeated
        # change 1% per fade_interval
        t = time.ticks_ms()
        if time.ticks_diff(t, t_fade_0) > fade_ms:

            if fade_state == 'down':  # day -> night
                if fade_percent < 100:
                    strip_rgb = get_fade_rgb(day_rgb, night_rgb, fade_percent)
                    set_strip(strip_rgb)
                    fade_percent += 1
                else:
                    prev_fade = fade_state
                    fade_state = 'hold'
                    hold_interval_s = night_hold_s
                    hold_start_ms = time.time()  # s

            elif fade_state == 'up':  # night -> day
                if fade_percent < 100:
                    strip_rgb = get_fade_rgb(night_rgb, day_rgb, fade_percent)
                    set_strip(strip_rgb)
                    fade_percent += 1
                else:
                    prev_fade = fade_state
                    fade_state = 'hold'
                    hold_interval_s = day_hold_s
                    hold_start_ms = time.time()  # s

            elif fade_state == 'hold':
                # hold phase over?
                if time.time() - hold_start_ms > hold_interval_s:
                    # set values for next fade
                    fade_state = 'up' if prev_fade == 'down' else 'down'
                    fade_percent = 0

            t_fade_0 = t  # set next interval start

    """
    # use time to control regular printout, if any
    t = time.ticks_ms()
    if time.ticks_diff(t, t_last_ms) > 1_000:  # every 1s
        t_last_ms = t
        # To display the current in Amps, uncomment the next line
        print("Current =", sense.read_current(), "A")
    """

    time.sleep(0.2)  # =< fade interval
