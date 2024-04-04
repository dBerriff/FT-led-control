""" model system state transitions """

import asyncio
import gc
from colour_space import ColourSpace
from plasma_2040 import Plasma2040
from ws2812 import Ws2812
from pixel_strip import PixelStrip
from v_time import VTime
from lcd_1602 import Lcd1602


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

    def __init__(self, board_, cs, nps, hsv_, vt, clock_hm_):
        self.board = board_
        self.cs = cs
        self.nps = nps
        self.hsv = hsv_
        self.vt = vt
        self.clock_hm = clock_hm_
        self.encode_rgb = nps.encode_rgb

        self.step_t_ms = 20
        # get gamma-corrected strip colours as 24-bit GRB value
        self.state_colour = {'day': cs.rgb_g(cs.hsv_rgb(hsv_['day'])),
                             'night': cs.rgb_g(cs.hsv_rgb(hsv_['night'])),
                             'off': (0, 0, 0)
                             }
        print(self.state_colour)
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
        self.nps.set_strip_rgb(self.state_colour[state])
        self.nps.write()

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
                
                self.state_colour = {'day': cs.rgb_g(cs.hsv_rgb(hsv_['day'])),
                     'night': cs.rgb_g(cs.hsv_rgb(hsv_['night'])),
                     'off': (0, 0, 0)
                     }

            """
            hsv_0 = self.hsv[state_0]
            hsv_1 = self.hsv[state_1]
            print(f'Fade {state_0} to {state_1} at {self.vt}')
            print(f'Fade {hsv_0} to {hsv_1}')
            delta_h = (hsv_1[0] - hsv_0[0]) / 100
            delta_s = (1.0 - hsv_0[1]) / 100
            delta_v = (hsv_1[2] - hsv_0[2]) / 100
            h_0 = hsv_0[0]
            s_0 = hsv_0[1]
            v_0 = hsv_0[2]
            h_inc = 0
            s_inc = 0
            v_inc = 0
            for i in range(101):
                h = h_0 + h_inc
                s = s_0 + s_inc
                v = v_0 + v_inc
                rgb = self.cs.rgb_g(self.cs.hsv_rgb((h, s, v)))
                self.nps.set_strip_rgb(rgb)
                self.nps.write()
                print(i, rgb)
                await asyncio.sleep_ms(20)
                h_inc += delta_h
                s_inc += delta_s
                v_inc += delta_v
                
            await asyncio.sleep_ms(1)

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


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def process_event(btn, system_):
        """ coro: passes button events to the system """
        while True:
            gc.collect()  # garbage collect before wait
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.state)
            btn.clear_state()

    async def show_time(vt_, lcd_):
        """ print virtual time every 1s in 'clock' state """
        while True:
            await system.clock_ev.wait()
            lcd_.write_line(0, vt_.get_time_hm())
            await asyncio.sleep_ms(1_000)

    # ====== parameters

    n_pixels = 30

    # system colours (no gamma correction)
    hsv = {
        'day': (240/360, 0.1, 0.95),
        'night': (359/360, 0.0, 0.3),
        'off': (0.0, 0.0, 0.0)
        }

    clock_hm = {'hm': '18:00', 'dawn': '06:00', 'dusk': '20:00'}
    clock_speed = 600

    # ====== end-of-parameters

    board = Plasma2040()
    driver = Ws2812(board.DATA)
    buttons = board.buttons
    nps = PixelStrip(driver, n_pixels)
    cs = ColourSpace()
    vt = VTime(s_inc=clock_speed)  # fast virtual clock
    lcd = Lcd1602(20, 21)
    lcd.write_line(0, 'Hello')
    print('Hello')
    
    system = DayNightST(board, cs, nps, hsv, vt, clock_hm)

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    print('System initialised')
    asyncio.create_task(show_time(system.vt, lcd))
    await asyncio.sleep(600)
    system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
