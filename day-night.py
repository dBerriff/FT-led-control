# day-night.py
"""
    Set LED strip using Pimoroni library
    written for Pimoroni Plasma 2040 board
    
    asyncio version
    No gamma correction
    
    - three buttons are used: A, B and User (labelled BOOT)
    - buttons have 2 states: 0: open; 1: pressed

    The system has 3 states:

    - 'off': all LEDs off; this is the start state.
        always returns system to 'off' state (does not stop code)

    - 'static': day/night illumination; A-button sets and toggles day/night

    - 'fade': fade from day to night and back repeatedly; B-button sets

    - print() statements confirm action: many or all of these can be deleted
    - elif statements with pass are "no action" statements included to show structure
"""

import asyncio
import plasma
from plasma import plasma2040
import time
from pimoroni import RGBLED, Analog
from buttons import Button


class Plasma2040:
    """
        Pimoroni Plasma 2040 board
        - control WS2812 LED strip
    """
    
    def __init__(self, n_leds):
        self.n_leds = n_leds
        self.buttons = {'A': Button(12, 'A'), 'B': Button(13, 'B'), 'U': Button(23, 'U')}
        self.led = RGBLED(plasma2040.LED_R, plasma2040.LED_G, plasma2040.LED_B)
        self.l_strip = plasma.WS2812(n_leds, 0, 0, plasma2040.DAT)

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb(*rgb_)

    def set_strip(self, rgb_):
        """ set whole strip to rgb_ """
        for i in range(self.n_leds):
            self.l_strip.set_rgb(i, *rgb_)

    def set_strip_level(self, rgb_, level):
        """
            set whole strip to adjusted level
            - level in range 0 - 255
            - no gamma correction in this version
        """
        r = rgb_[0] * level // 255
        g = rgb_[1] * level // 255
        b = rgb_[2] * level // 255
        self.set_strip((r, g, b))


class LightingST:
    """ system: lighting state-transition logic """

    day_rgb = (90, 80, 45)
    night_rgb = (10, 30, 80)
    off_rgb = (0, 0, 0)
    led_red = (32, 0, 0)
    led_green = (0, 32, 0)
    led_blue = (0, 0, 32)
    hold_period = 15  # s

    def __init__(self, board):  # Plasma2040
        self.board = board
        self.state = 'off'  # 'static', 'fade'
        self.strip_rgb = self.off_rgb
        self.board.set_onboard(self.led_red)

        self.day_night = 'day'
        self.fade_deltas = (0, 0, 0)
        self.fade_count = 0
        self.fade = 'down'  # 'down' or 'up'
        self.t_fade_0 = time.ticks_ms()
        self.fade_percent = 0
        self.prev_fade = 'up'
        self.hold_start_ms = 0

    def change_state(self, btn_name):
        """
            respond to button event
            - pass button-event name to current state
        """
        print(f'event: button {btn_name} pressed state: {self.state}')

        if self.state == 'off':
            if btn_name == 'A':
                print('Set state "static"')
                self.state = 'static'
                self.day_night = 'day'
                self.strip_rgb = self.day_rgb
                self.board.set_onboard(self.led_green)
            elif btn_name == 'B':
                print('Set state "fade"')
                self.state = 'fade'
                self.day_night = 'day'
                self.strip_rgb = self.day_rgb
                self.fade = 'down'
                self.fade_percent = 0
                self.t_fade_0 = time.ticks_ms()
                self.board.set_onboard(self.led_blue)
            elif btn_name == 'U':
                pass
            self.board.set_strip(self.strip_rgb)

        elif self.state == 'static':
            if btn_name == 'A':
                # toggle between day and night
                if self.day_night == 'day':
                    print('Set night')
                    self.day_night = 'night'
                    self.strip_rgb = self.night_rgb
                else:
                    print('Set day')
                    self.day_night = 'day'
                    self.strip_rgb = self.day_rgb
            elif btn_name == 'B':
                pass
            elif btn_name == 'U':
                print('Set state "off"')
                self.state = 'off'
                self.strip_rgb = self.off_rgb
                self.board.set_onboard(self.led_red)
            self.board.set_strip(self.strip_rgb)

        elif self.state == 'fade':
            if btn_name == 'A':
                pass
            elif btn_name == 'B':
                pass
            elif btn_name == 'U':
                print('Set state "off"')
                self.state = 'off'
                self.strip_rgb = self.off_rgb
                self.board.set_onboard(self.led_red)
            self.board.set_strip(self.strip_rgb)

    async def fade(self):
        """ fade from rgb_0 to rgb_1 """
        pass
        await asyncio.sleep_ms(0)


    @staticmethod
    def get_fade_rgb(rgb_0, rgb_1, percent):
        """
            return the current fade rgb value
            - inefficient but tests the concept
        """
        r = rgb_0[0] + (rgb_1[0] - rgb_0[0]) * percent // 100
        g = rgb_0[1] + (rgb_1[1] - rgb_0[1]) * percent // 100
        b = rgb_0[2] + (rgb_1[2] - rgb_0[2]) * percent // 100
        return r, g, b


async def main():
    """ initialise then run tasks under asyncio scheduler """
    
    async def keep_alive_ms(duration):
        """ """
        await asyncio.sleep_ms(duration)

    async def process_event(btn, system_):
        """ passes button events to the system """

        while True:
            await btn.press_ev.wait()
            system_.change_state(btn.name)
            btn.clear_state()

    # ====== parameters

    n_leds = 30

    # ====== end-of-parameters

    # buttons are hard-wired on the Plasma 2040
    buttons = {'A': Button(12, 'A'), 'B': Button(13, 'B'), 'U': Button(23, 'U')}

    board = Plasma2040(n_leds)
    board.l_strip.start()
    system = LightingST(board)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())
        asyncio.create_task(process_event(buttons[b], system))
    print('System initialised')

    await keep_alive_ms(60_000)  # test duration


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
