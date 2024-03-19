# pio_day-night.py
"""
    Set LED strip using pio_ws2812 module (adapted from Pico docs)
    - class Plasma2040: written for Pimoroni Plasma 2040 board
    - class LightingST: models lighting states and state-transition logic
    
    asyncio version
    
    - 3 + 1 buttons are hard-wired on the Pimoroni Plasma 2040:
        A, B and User (labelled BOOT); and RESET which resets the processor
    - button-click is an event and passed as button name:
        'A', 'B' or 'U'

    The system has 4 states:

    - 'off': all WS2812 LEDs off; this is the start state.
        'U' button returns system to 'off' (does not stop code)

    - 'day': day illumination; 'A' button sets and toggles to night

    - 'night': night illumination; 'A' button sets and toggles to day

    - 'fade': repeat: hold day, fade to night, hold night, fade to day; 'B' button sets

"""

import asyncio
from machine import Pin, freq
import gc
from plasma import plasma2040
from pimoroni import RGBLED, Analog
from buttons import Button
from pio_ws2812 import Ws2812Strip
from colour_space import RGB, ColourSpace
from v_time import VTime


class Plasma2040(Ws2812Strip):
    """
        Pimoroni Plasma 2040 board
        - control WS2812 LED strip
        - hardwired GPIO pins (see schematic):
            CLK 3V3: 14, DATA 3V3: 15  : clock and data to 5V logic-shift
            LED_R: 16, LED_G: 17, LED_B: 18  : onboard 3-colour LED
            SW_A: 12, SW_B: 13, SW_U: 23  : user buttons
    """
    
    def __init__(self, n_pixels_):
        super().__init__(Pin(15, Pin.OUT), n_pixels_)
        self.buttons = {'A': Button(12, 'A'),
                        'B': Button(13, 'B'),
                        'U': Button(23, 'U')
                        }
        self.led = RGBLED(plasma2040.LED_R, plasma2040.LED_G, plasma2040.LED_B)

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb(*rgb_)


class DayNightST:
    """
        lighting State-Transition logic
        - dict stores event: transitions
        - add await to fade transitions for event to propagate
    """

    # onboard LED colours confirm button press
    led_rgb = {
        'off': (32, 0, 0),
        'day': (0, 32, 0),
        'night': (0, 8, 0),
        'fade': (0, 0, 32)
        }

    def __init__(self, board, np_rgb, vt_):
        self.board = board
        self.np_rgb = np_rgb
        self.vt = vt_
        self.Vhm = vt_.Vhm  # namedtuple
        self.step_t_ms = 200
        self.cs = ColourSpace()
        self.np_rgb_g = {'day': self.cs.get_rgb_g(np_rgb['day']),
                         'night': self.cs.get_rgb_g(np_rgb['night']),
                         'off': RGB(0, 0, 0)
                         }
        self.day_night = ''
        self.fade_ev = asyncio.Event()
        self.state = self.set_off()
        self.board.set_onboard(self.led_rgb['off'])

        # event: state-transition logic
        self.transitions = {
            'off': {'A': self.set_day, 'B': self.set_by_clock, 'U': self.no_t},
            'day': {'A': self.set_night, 'B': self.no_t, 'U': self.set_off},
            'night': {'A': self.set_day, 'B': self.no_t, 'U': self.set_off},
            'fade': {'A': self.no_t, 'B': self.no_t, 'U': self.set_off}
            }

    # transition methods: each must return state
    def set_off(self):
        """ set parameters for off """
        print('Set state "off"')
        self.fade_ev.clear()  # ends fade task if running
        self.board.set_strip(self.np_rgb_g['off'])
        self.board.write()
        return 'off'

    def set_day(self):
        """ set parameters for day """
        print('Set state "day"')
        self.board.set_strip(self.np_rgb_g['day'])
        self.board.write()
        return 'day'

    def set_night(self):
        """ set parameters for night """
        print('Set state "night"')
        self.board.set_strip(self.np_rgb_g['night'])
        self.board.write()
        return 'night'

    def set_by_clock(self):
        """ set parameters for fade """
        print('Set state "fade"')
        self.fade_ev.set()
        self.vt.time_hm = self.Vhm(12, 0)
        asyncio.create_task(self.clock_transitions())
        return 'fade'

    def no_t(self):
        """ no transition """
        return self.state

    async def state_transition_logic(self, btn_name):
        """ coro: invoke transition for state & button-press event """
        self.state = self.transitions[self.state][btn_name]()
        self.board.set_onboard(self.led_rgb[self.state])
        await asyncio.sleep_ms(20)  # allow any transition tasks to start/end

    async def clock_transitions(self):
        """ coro: fade day/night/hold output while fade_ev.is_set """

        async def fade(state_0, state_1):
            """
                coro: fade-and-hold single transition
                - linear fade with each result gamma corrected
            """
            print(f'In fade {state_0} {state_1}')
            rgb_0 = self.np_rgb[state_0]
            rgb_1 = self.np_rgb[state_1]
            fade_percent = 0
            while fade_percent < 101 and self.fade_ev.is_set():
                self.board.set_strip(
                    self.cs.get_rgb_g(self.get_fade_rgb(rgb_0, rgb_1, fade_percent)))
                self.board.write()
                await asyncio.sleep_ms(self.step_t_ms)
                fade_percent += 1
                
        print('Entered clock transitions')
        # clear any previous Event setting; initialise state
        self.vt.change_state_ev.clear()
        if self.vt.state == 'day':
            self.set_day()
        else:
            self.set_night()
        # fade raw rgb and apply gamma correction at set_strip()
        while self.fade_ev.is_set():
            if self.vt.change_state_ev.is_set():
                self.vt.change_state_ev.clear()
                if self.vt.state == 'night':
                    await fade('day', 'night')
                else:
                    await fade('night', 'day')

            await asyncio.sleep_ms(1000)
        print('End fade_transitions()')

    @staticmethod
    def get_fade_rgb(rgb_0_, rgb_1_, percent_):
        """ return percentage rgb value """
        r = rgb_0_.r + (rgb_1_.r - rgb_0_.r) * percent_ // 100
        g = rgb_0_.g + (rgb_1_.g - rgb_0_.g) * percent_ // 100
        b = rgb_0_.b + (rgb_1_.b - rgb_0_.b) * percent_ // 100
        return RGB(r, g, b)


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def process_event(btn, system_):
        """ coro: passes button events to the system """
        while True:
            gc.collect()  # garbage collect before wait
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.name)
            btn.clear_state()

    async def show_time(vt_):
        """ print virtual time at set intervals """
        while True:
            print(vt_)
            await asyncio.sleep_ms(1_000)

    # ====== parameters

    n_pixels = 30
    # linear system-state colours (no gamma correction)
    rgb = {
        'day': RGB(90, 80, 45),
        'night': RGB(10, 30, 80),
        'off': RGB(0, 0, 0)
        }

    # ====== end-of-parameters

    vt = VTime(720)
    vt.start_clock()
    await asyncio.sleep_ms(20)

    board = Plasma2040(n_pixels)
    buttons = board.buttons  # hard-wired on Plasma 2040
    system = DayNightST(board, rgb, vt)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    print('System initialised')
    await show_time(vt)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
