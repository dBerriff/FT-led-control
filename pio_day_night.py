# day-night.py
"""
    Set LED strip using Pimoroni library
    written for Pimoroni Plasma 2040 board
    
    asyncio version
    
    - 3 + 1 buttons are hard-wired on the Pimoroni Plasma 2040:
        A, B and User (labelled BOOT); and RESET which resets the processor
    - button-click is an event and passed as button name:
        'A', 'B' or 'U'

    The system has 3 states:

    - 'off': all WS2812 LEDs off; this is the start state.
        'U' button returns system to 'off' (does not stop code)

    - 'day_night': day/night illumination; 'A' button sets and toggles day/night

    - 'fade': fade from day to night and back repeatedly; 'B' button sets

    - print() statements confirm action: many or all of these can be deleted

    class Plasma2040: models Pimoroni Plasma 2040 board
    class LightingST: models lighting states and state-transition logic

"""

import asyncio
from machine import Pin, freq
import gc
from plasma import plasma2040
from pimoroni import RGBLED, Analog
from buttons import Button
from pio_ws2812 import Ws2812Strip
from colour_space import ColourSpace


class Plasma2040(Ws2812Strip):
    """
        Pimoroni Plasma 2040 board
        - control WS2812 LED strip
        - hardwired GPIO pins (see schematic):
            CLK 3V3: 14, DATA 3V3: 15  : pixel-strip clock and data to 5V logic-shift
            LED_R: 16, LED_G: 17, LED_B: 18  : onboard 3-colour LED
            SW_A: 12, SW_B: 13, SW_U: 23  : user buttons
    """
    
    def __init__(self, n_pixels_):
        super().__init__(Pin(15, Pin.OUT), n_pixels_)
        self.buttons = {'A': Button(12, 'A'), 'B': Button(13, 'B'), 'U': Button(23, 'U')}
        self.led = RGBLED(plasma2040.LED_R, plasma2040.LED_G, plasma2040.LED_B)

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb(*rgb_)

    def set_strip(self, rgb_):
        """ set all pixels to rgb_ """
        for i in range(self.n_pixels):
            self.set_pixel(i, rgb_)


class LightingST:
    """
        lighting State-Transition logic
        - dict stores event: transitions
        - add await to fade transitions for event to propagate
    """
    # onboard LED colours confirm button press
    led_rgb = {'off': (32, 0, 0), 'day_night': (0, 32, 0), 'fade': (0, 0, 32)}

    def __init__(self, board, np_rgb, hold_t_s=5, step_t_ms=200):
        self.board = board
        self.np_rgb = np_rgb
        self.hold_t_s = hold_t_s
        self.step_t_ms = step_t_ms
        self.cs = ColourSpace()
        self.np_rgb_g = {'day': self.cs.get_rgb_g(np_rgb['day']),
                         'night': self.cs.get_rgb_g(np_rgb['night']),
                         'off': (0, 0, 0)
                         }
        self.day_night = ''
        self.fade_ev = asyncio.Event()
        self.state = self.set_off()
        self.board.set_onboard(self.led_rgb['off'])

        # state-transition logic
        self.transitions = {
            'off': {'A': self.set_day_night, 'B': self.set_fade, 'U': self.no_t},
            'day_night': {'A': self.set_day_night, 'B': self.no_t, 'U': self.set_off},
            'fade': {'A': self.no_t, 'B': self.no_t, 'U': self.set_off}
            }

    # transition methods: each must return state
    def set_off(self):
        """ set parameters for off """
        print('Set state "off"')
        self.day_night = ''
        self.fade_ev.clear()
        self.board.set_strip(self.np_rgb_g['off'])
        self.board.write()
        return 'off'

    def set_fade(self):
        """ set parameters for fade """
        print('Set state "fade"')
        self.fade_ev.set()
        asyncio.create_task(self.fade_transitions())
        return 'fade'

    def set_day_night(self):
        """ set or toggle static output """
        if self.day_night == 'day':
            print('Set state "day_night" night')
            self.day_night = 'night'
            self.board.set_strip(self.np_rgb_g['night'])
            self.board.write()
        else:
            print('Set state "day_night" day')
            self.day_night = 'day'
            self.board.set_strip(self.np_rgb_g['day'])
            self.board.write()
        return 'day_night'

    def no_t(self):
        """ no transition """
        return self.state

    async def state_transition_logic(self, btn_name):
        """ coro: invoke transition for state & button-press event """
        self.state = self.transitions[self.state][btn_name]()
        self.board.set_onboard(self.led_rgb[self.state])
        await asyncio.sleep_ms(20)  # allow for task/event processing

    async def fade_transitions(self):
        """ coro: fade day/night/hold output when fade_ev.is_set """

        async def fade_hold(rgb_0, rgb_1):
            """
                coro: fade-and-hold single transition
                - linear fade with each result gamma corrected
            """
            fade_percent = 0
            while fade_percent < 101 and self.fade_ev.is_set():
                self.board.set_strip(
                    self.cs.get_rgb_g(self.get_fade_rgb(rgb_0, rgb_1, fade_percent)))
                self.board.write()
                await asyncio.sleep_ms(self.step_t_ms)
                fade_percent += 1
            t = 0  # s
            while t < self.hold_t_s and self.fade_ev.is_set():
                await asyncio.sleep(1)
                t += 1

        print('Start fade_transitions()')
        # fade raw rgb and apply gamma correction at set_strip()
        while self.fade_ev.is_set():
            await fade_hold(self.np_rgb['day'], self.np_rgb['night'])
            await fade_hold(self.np_rgb['night'], self.np_rgb['day'])
        print('End fade_transitions()')

    @staticmethod
    def get_fade_rgb(rgb_0_, rgb_1_, percent_):
        """ return percentage rgb value """
        r = rgb_0_[0] + (rgb_1_[0] - rgb_0_[0]) * percent_ // 100
        g = rgb_0_[1] + (rgb_1_[1] - rgb_0_[1]) * percent_ // 100
        b = rgb_0_[2] + (rgb_1_[2] - rgb_0_[2]) * percent_ // 100
        return r, g, b


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """
    
    async def keep_alive():
        """ coro to be awaited """
        while True:
            await asyncio.sleep(1)

    async def process_event(btn, system_):
        """ passes button events to the system """
        while True:
            gc.collect()  # garbage collect before wait
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.name)
            btn.clear_state()

    # ====== parameters

    n_pixels = 30
    rgb = {'day': (90, 80, 45),
           'night': (10, 30, 80),
           'off': (0, 0, 0)
           }

    # ====== end-of-parameters

    board = Plasma2040(n_pixels)
    buttons = board.buttons  # hard-wired on Plasma 2040
    system = LightingST(board, rgb)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    print('System initialised')

    await keep_alive()  # keep scheduler running


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
