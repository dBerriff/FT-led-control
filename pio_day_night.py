# pio_day-night.py
"""
    Set LED strip using pio_ws2812 module (adapted from Pico docs)
    - class Plasma2040: written for Pimoroni Plasma 2040 board
    - class LightingST: models lighting states and state-transition logic
    
    asyncio version
    
    - 3 + 1 buttons are hard-wired on the Pimoroni Plasma 2040:
        A, B, U (user, labelled BOOT) + RESET
    - button-click (1) and button-hold (2) are events;
        -- passed back as [button-name + event-number]
        -- <click>: 'A1', 'B1', 'U1'; <hold>: 'U2'

    The system has 4 states:

    - 'off': all WS2812 LEDs off; this is the start state.
        'U': button returns system to 'off' (does not stop code)

    - 'day': day illumination; 'A': button sets and toggles to night

    - 'night': night illumination; 'A': button toggles to day

    - 'clock': day, sunset, night, sunrise; set by virtual clock;
        'B': button-click sets; button-hold restarts the clock

"""

import asyncio
from machine import Pin, freq
from micropython import const
import gc
from pimoroni import RGBLED, Analog
from buttons import Button, HoldButton
from pio_ws2812 import Ws2812Strip
from colour_space import RGB, ColourSpace
from v_time import VTime


class Plasma2040(Ws2812Strip):
    """
        Pimoroni Plasma 2040 board
        - control WS2812 LED strip
        - hardwired GPIO pins (see schematic and constants below):
            -- CLK, DATA: LED strip clock and data
            -- LED_R, LED_G, LED_B: onboard 3-colour LED
            -- SW_A, SW_B, SW_U: user buttons
    """

    SW_A = const(12)
    SW_B = const(13)
    SW_U = const(23)

    CLK = const(14)
    DATA = const(15)

    LED_R = const(16)
    LED_G = const(17)
    LED_B = const(18)

    def __init__(self, n_pixels_):
        super().__init__(Pin(self.DATA, Pin.OUT), n_pixels_)
        self.buttons = {'A': Button(self.SW_A, 'A'),
                        'B': HoldButton(self.SW_B, 'B'),
                        'U': Button(self.SW_U, 'U')
                        }
        self.led = RGBLED(self.LED_R, self.LED_G, self.LED_B)

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
        'clock': (0, 0, 32)
        }

    def __init__(self, board, np_rgb):
        self.board = board
        self.np_rgb = np_rgb
        self.vt = VTime()
        self.vhm = self.vt.Vhm  # namedtuple
        self.step_t_ms = 200
        self.cs = ColourSpace()
        self.np_rgb_g = {'day': self.cs.get_rgb_g(np_rgb['day']),
                         'night': self.cs.get_rgb_g(np_rgb['night']),
                         'off': RGB(0, 0, 0)
                         }
        self.day_night = ''
        self.init_time = self.vhm(12, 0)
        self.sunrise = self.vhm(6, 0)
        self.sunset = self.vhm(20, 0)

        self.clock_ev = asyncio.Event()
        self.state = self.set_off()
        self.board.set_onboard(self.led_rgb['off'])

        # event: state-transition logic
        # button state is key: value is transition function name
        self.transitions = {
            'off': {'A1': self.set_day, 'B1': self.set_by_clock, 'U1': self.no_t},
            'day': {'A1': self.set_night, 'B1': self.no_t, 'U1': self.set_off},
            'night': {'A1': self.set_day, 'B1': self.no_t, 'U1': self.set_off},
            'clock': {'A1': self.no_t, 'B1': self.no_t, 'B2': self.set_by_clock, 'U1': self.set_off}
            }

    # set LED strip display state

    def set_strip(self, state):
        """ set strip to state """
        self.board.fill_array(self.np_rgb_g[state])
        self.board.write()

    # state-transition methods

    def set_off(self):
        """ set state """
        print('Set state "off"')
        self.clock_ev.clear()  # end fade task if running
        self.vt.run_ev.clear()
        self.set_strip('off')
        return 'off'

    def set_day(self):
        """ set state """
        print('Set state "day"')
        self.set_strip('day')
        return 'day'

    def set_night(self):
        """ set state """
        print('Set state "night"')
        self.set_strip('night')
        return 'night'

    def set_by_clock(self):
        """ set state """
        print('Set state "clock"')
        self.clock_ev.set()
        self.vt.start_clock(self.init_time, self.sunrise, self.sunset)
        asyncio.create_task(self.clock_transitions())
        return 'clock'

    def no_t(self):
        """ no transition """
        return self.state

    # transition methods

    async def state_transition_logic(self, btn_state):
        """ coro: invoke transition for state & button-press event """
        transitions = self.transitions[self.state]
        if btn_state in transitions:
            self.state = transitions[btn_state]()  # call method
        self.board.set_onboard(self.led_rgb[self.state])
        await asyncio.sleep_ms(20)  # allow transition tasks to start/end

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """
                coro: fade-and-hold single transition
                - linear fade with each result gamma corrected
            """
            print(f'Fade {state_0} to {state_1} at {self.vt}')
            rgb_0 = self.np_rgb[state_0]
            rgb_1 = self.np_rgb[state_1]
            fade_percent = 0
            while fade_percent < 101 and self.clock_ev.is_set():
                self.board.fill_array(
                    self.cs.get_rgb_g(self.get_fade_rgb(rgb_0, rgb_1, fade_percent)))
                self.board.write()
                await asyncio.sleep_ms(self.step_t_ms)
                fade_percent += 1
                
        # clear any previous Event setting; initialise state
        self.vt.change_state_ev.clear()
        self.set_strip(self.vt.state)
        # fade rgb between states
        while self.clock_ev.is_set():  # cleared if OFF pressed
            if self.vt.change_state_ev.is_set():
                # consumer must clear Event
                self.vt.change_state_ev.clear()
                if self.vt.state == 'night':
                    await fade('day', 'night')
                else:
                    await fade('night', 'day')

            await asyncio.sleep_ms(1000)

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
            await system_.state_transition_logic(btn.state)
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
    """
    rgb = {'day': RGB(225, 200, 112),
           'night': RGB(25, 75, 200),
           'off': RGB(0, 0, 0)
           }
    """

    # ====== end-of-parameters

    board = Plasma2040(n_pixels)
    buttons = board.buttons  # hard-wired on Plasma 2040
    system = DayNightST(board, rgb)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    print('System initialised')
    asyncio.create_task(show_time(system.vt))
    await asyncio.sleep(120)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
