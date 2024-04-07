
# state_transition.py
""" model ambient light state transitions """

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

    lcd_str = {
        'blank': '  '.center(16),
        'state': 'State'.center(16),
        'off': 'off'.center(16),
        'day': 'day'.center(16),
        'night': 'night'.center(16),
        'clock': 'clock'.center(16)
    }

    def __init__(self, cs, nps, vt, lcd_):
        self.cs = cs
        self.nps = nps
        self.vt = vt
        self.lcd = lcd_
        self.state = None
        # methods build dicts from user parameters 
        self.state_hsv = {}
        self.state_rgb = {}
        self.clock_s = {}
        # clock_ev is set when in state 'clock'
        self.clock_ev = asyncio.Event()

        # state-transition logic
        # button-event: as key within a state; value is the transition method name
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
    def build_state_colour_dicts(self, state_hsv_):
        """
            load HSV and RGB dicts with state as key
            - HSV for day/night transition
            - RGB for static colours
        """
        for key in state_hsv_:
            self.state_hsv[key] = state_hsv_[key]
            self.state_rgb[key] = self.cs.rgb_g(self.cs.hsv_rgb(state_hsv_[key]))

    def set_clock_s(self, clock_hm_):
        """ set state RGB values from HSV values """
        for hm in clock_hm_:
            h_m_tokens = clock_hm_[hm].split(':')
            self.clock_s[hm] = int(h_m_tokens[0]) * 3600 + int(h_m_tokens[1]) * 60

    def write_strip_by_state(self, state):
        """ set strip to state colour """
        self.nps.set_strip_rgb(self.state_rgb[state])
        self.nps.write()

    # state-transition methods

    def set_off(self):
        """ set state """
        self.clock_ev.clear()  # end fade task if running
        self.vt.run_ev.clear()  # stop clock if running
        self.write_strip_by_state('off')
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['off'])
        self.state = 'off'

    def set_day(self):
        """ set state """
        self.write_strip_by_state('day')
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['day'])
        self.state = 'day'

    def set_night(self):
        """ set state """
        self.write_strip_by_state('night')
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['night'])
        self.state = 'night'

    def set_by_clock(self):
        """ set state """
        self.vt.start_ticks(self.clock_s['hm'],
                            self.clock_s['dawn'],
                            self.clock_s['dusk'])
        asyncio.create_task(self.clock_transitions())
        self.clock_ev.set()
        self.lcd.write_line(0, self.lcd_str['blank'])
        self.lcd.write_line(1, self.lcd_str['clock'])
        self.state = 'clock'

    def no_t(self):
        """ no transition """
        return self.state

    # transition methods

    async def state_transition_logic(self, btn_state):
        """ coro: invoke transition for state & button-press event """
        transitions = self.transitions[self.state]
        if btn_state in transitions:
            transitions[btn_state]()  # invoke transition method
        await asyncio.sleep_ms(20)  # allow scheduler to run tasks

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """ coro: fade-and-hold single transition """

            async def do_fade(state_0_, state_1_):
                """ do the fade """
                h_0, s_0, v_0 = self.state_hsv[state_0_]
                d_h = (self.state_hsv[state_1_][0] - h_0) / 100
                d_s = (self.state_hsv[state_1_][1] - s_0) / 100
                d_v = (self.state_hsv[state_1_][2] - v_0) / 100
                for i in range(100):
                    rgb = self.cs.rgb_g(self.cs.hsv_rgb((h_0, s_0, v_0)))
                    self.nps.set_strip_rgb(rgb)
                    self.nps.write()
                    await asyncio.sleep_ms(40)
                    h_0 += d_h
                    s_0 += d_s
                    v_0 += d_v
                # ensure target state is set
                self.write_strip_by_state(state_1_)
                await asyncio.sleep_ms(1)

            await do_fade(state_0, 'mid')
            await do_fade('mid', state_1)

        # clear any previous Event setting; initialise state
        self.vt.change_state_ev.clear()
        self.write_strip_by_state(self.vt.state)
        # fade rgb between states
        while self.clock_ev.is_set():  # cleared if OFF pressed
            initial_state = self.vt.state
            await self.vt.change_state_ev.wait()
            if initial_state == 'day':
                target_state = 'night'
            else:
                target_state = 'day'
            # consumer must clear Event
            self.vt.change_state_ev.clear()
            await fade(initial_state, target_state)
            await asyncio.sleep_ms(20)


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def process_event(btn, system_):
        """ coro: passes button events to the system """
        while True:
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.state)
            btn.clear_state()

    async def show_time(vt_, lcd_, clock_s_):
        """ print virtual time every 1s in 'clock' state """
        day_str = 'day'.center(16)
        night_str = 'night'.center(16)
        day_s = clock_s_['dawn']
        night_s = clock_s_['dusk']
        while True:
            await system.clock_ev.wait()
            s = vt_.get_day_s()
            time_str = vt_.get_time_hm().center(16)
            if day_s <= s < night_s:
                p_str = day_str
            else:
                p_str = night_str

            lcd_.write_line(0, time_str)
            lcd_.write_line(1, p_str)
            gc.collect()
            await asyncio.sleep_ms(1_000)

    # ====== parameters

    n_pixels = 30

    # state colours as HSV
    state_hsv = {
        'day': (240/360, 0.1, 0.95),
        'night': (359/360, 0.0, 0.15),
        'mid': (359/360, 1.0, 0.5),
        'off': (0.0, 0.0, 0.0)
        }

    clock_hm = {'hm': '18:00', 'dawn': '06:00', 'dusk': '20:00'}
    clock_speed = 1200

    # ====== end-of-parameters

    # instantiate system objects
    cs = ColourSpace()
    board = Plasma2040()
    driver = Ws2812(board.DATA)
    nps = PixelStrip(driver, n_pixels)
    buttons = board.buttons
    lcd = Lcd1602(20, 21)  # Plasma 2040 I2C pin-outs
    vt = VTime(s_inc=clock_speed)  # fast virtual clock
    system = DayNightST(cs, nps, vt, lcd)
    # initialise
    board.set_onboard((0, 15, 0))  # on
    system.build_state_colour_dicts(state_hsv)
    system.set_clock_s(clock_hm)
    lcd.initialise()  # show state when set
    system.set_off()
    print('System initialised')

    # create tasks to pass press_ev events to system
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event

    await show_time(system.vt, lcd, system.clock_s)

    system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
