# pio_day-night.py
"""
    Set LED strip using pio_ws2812 module (adapted from Pico docs)
    - class Plasma2040: written for Pimoroni Plasma 2040 p_2040
    - class LightingST: models lighting states and state-transition logic
    
    asyncio version
    
    - 3 + 1 buttons are hard-wired on the Pimoroni Plasma 2040:
        A, B, U (user, labelled BOOT) + RESET
    - button-click (1) and button-hold (2) are events;
        -- passed back as [button-name + event-number]
        -- <click>: 'A1', 'B1', 'U1'; <hold>: 'U2'

    The system has 4 states:

    - 'off': all WS2812 LEDs off; this is the start state.
        'U': button returns to state 'off'

    - 'day': day illumination; 'A': button sets and toggles to night

    - 'night': night illumination; 'A': button toggles to day

    - 'clock_hm': day, _dusk, night, _dawn; set by virtual clock;
        'B': button-click sets; button-hold restarts the clock

"""

import asyncio
from machine import Pin, freq
from micropython import const
import gc
from buttons import Button, HoldButton
from led_pwm import PimoroniRGB
from pio_ws2812 import Ws2812Strip
from v_time import VTime


class Plasma2040(Ws2812Strip):
    """
        Pimoroni Plasma 2040 p_2040
        - control WS2812 LED strip
        - hardwired GPIO pins (see schematic and constants below):
            -- CLK, DATA: LED strip clock and data
            -- LED_R, LED_G, LED_B: onboard 3-grb_ LED
            -- SW_A, SW_B, SW_U: user buttons
    """
    # Plasma 2040 GPIO pins
    SW_A = const(12)
    SW_B = const(13)
    SW_U = const(23)

    CLK = const(14)  # not used for WS2812
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
        self.led = PimoroniRGB(self.LED_R, self.LED_G, self.LED_B)

    def set_onboard(self, rgb_):
        """ set onboard LED to rgb_ """
        self.led.set_rgb_u8(*rgb_)


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

    def __init__(self, p_2040, np_rgb, vt, clock_hm_):
        self.board = p_2040
        self.np_rgb = np_rgb
        self.clock_hm = clock_hm_
        self.vt = vt
        self.step_t_ms = 20
        # set gamma-corrected strip colours as 24-bit GRB value
        self.state_colour = {'day': self.board.encode_g(np_rgb['day']),
                             'night': self.board.encode_g(np_rgb['night']),
                             'off': 0
                             }
        self.day_night = ''
        # set clock_ev when in state 'clock'
        self.clock_ev = asyncio.Event()
        self.state = self.set_off()
        self.board.set_onboard(self.led_rgb['off'])

        # state-transition logic
        # button-event is the key within a state: the value is transition method name
        self.transitions = {
            'off': {'A1': self.set_day, 'B1': self.set_by_clock, 'U1': self.no_t},
            'day': {'A1': self.set_night, 'B1': self.no_t, 'U1': self.set_off},
            'night': {'A1': self.set_day, 'B1': self.no_t, 'U1': self.set_off},
            'clock': {'A1': self.no_t,
                      'B1': self.no_t, 'B2': self.set_by_clock,
                      'U1': self.set_off
                      }
            }

    # set LED strip display state

    def set_strip(self, state):
        """ set strip to state colour, gamma corrected """
        self.board.set_strip(self.state_colour[state])
        self.board.write()

    # state-transition methods

    def set_off(self):
        """ set state """
        print('Set state "off"')
        self.clock_ev.clear()  # end fade task if running
        self.vt.run_ev.clear()  # stop clock if running
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
        self.vt.start_clock(self.clock_hm['hm'],
                            self.clock_hm['dawn'],
                            self.clock_hm['dusk'])
        asyncio.create_task(self.clock_transitions())
        self.clock_ev.set()
        return 'clock'

    def no_t(self):
        """ no transition """
        return self.state

    # transition methods

    async def state_transition_logic(self, btn_state):
        """ coro: invoke transition for state & button-press event """
        transitions = self.transitions[self.state]
        if btn_state in transitions:
            self.state = transitions[btn_state]()  # invoke transition method
        self.board.set_onboard(self.led_rgb[self.state])
        await asyncio.sleep_ms(20)  # allow scheduler to run tasks

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """
                coro: fade-and-hold single transition
                - linear fade with each result gamma corrected
                *** Convert to HSV transition
            """
            print(f'Fade {state_0} to {state_1} at {self.vt}')
            rgb_0 = self.np_rgb[state_0]
            rgb_1 = self.np_rgb[state_1]
            fade_percent = 0
            while fade_percent < 101 and self.clock_ev.is_set():
                self.board.set_strip(
                    self.board.encode_g(
                        self.get_fade_rgb(rgb_0, rgb_1, fade_percent)))
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

            await asyncio.sleep_ms(20)

    @staticmethod
    def get_fade_rgb(rgb_0_, rgb_1_, percent_):
        """ return percentage rgb value """
        r = rgb_0_[0] + (rgb_1_[0] - rgb_0_[0]) * percent_ // 100
        g = rgb_0_[1] + (rgb_1_[1] - rgb_0_[1]) * percent_ // 100
        b = rgb_0_[2] + (rgb_1_[2] - rgb_0_[2]) * percent_ // 100
        return r, g, b


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
        """ print virtual time every 1s in 'clock' state """
        while True:
            await system.clock_ev.wait()
            print(vt_, end='\r')
            await asyncio.sleep_ms(1_000)

    # ====== parameters

    n_pixels = 30

    # system colours (no gamma correction)
    rgb = {
        'day': (128, 128, 128),
        'night': (32, 32, 36),
        'off': (0, 0, 0)
        }

    clock_hm = {'hm': '18:00', 'dawn': '06:00', 'dusk': '20:00'}
    clock_speed = 600

    # ====== end-of-parameters

    p_2040 = Plasma2040(n_pixels)
    buttons = p_2040.buttons  # hard-wired on Plasma 2040
    vt = VTime(s_inc=clock_speed)  # fast virtual clock
    system = DayNightST(p_2040, rgb, vt, clock_hm)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    print('System initialised')
    asyncio.create_task(show_time(system.vt))
    await asyncio.sleep(600)
    system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
