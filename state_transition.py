# state_transition.py
""" model ambient light state transitions """

import asyncio
import gc
from colour_space import ColourSpace
from lcd_1602 import Lcd1602
from pixel_strip import PixelStrip
from plasma_2040 import Plasma2040
from v_time import VTime
from ws2812 import Ws2812


class DayNightST:
    """
        lighting State-Transition logic
        - dict stores event: transitions
        - add await to fade transitions for event to propagate
        - vt instantiates [clock_]run_ev
        - vt instantiates and sets change_state_ev
    """

    lcd_str = {
        'blank': ''.center(16),
        'state': 'State'.center(16),
        'off': 'off'.center(16),
        'day': 'day'.center(16),
        'night': 'night'.center(16),
        'clock': 'clock'.center(16)
    }

    def __init__(self, cs, nps, vt, lcd_, **kwargs):
        self.cs = cs
        self.nps = nps
        self.vt = vt
        self.lcd = lcd_
        self.state = None
        self.fade_flag = False

        # methods build dicts from user parameters 
        self.state_hsv = {}
        self.state_rgb = {}
        for arg in kwargs:
            if arg == 'hsv':
                self.build_state_colour_dicts(kwargs[arg])
            elif arg == 'hm':
                self.hm_dict = kwargs[arg]

        # state-transition logic
        # button-event: as key within a state; value is the transition method name
        self.transitions = {
            'off': {'A1': self.set_day,
                    'B1': self.set_by_clock,
                    'U1': self.no_t},
            'day': {'A1': self.set_night,
                    'B1': self.no_t,
                    'U1': self.set_off},
            'night': {'A1': self.set_day,
                      'B1': self.no_t,
                      'U1': self.set_off},
            'clock': {'A1': self.no_t,
                      'B1': self.no_t,
                      'B2': self.set_by_clock,
                      'U1': self.set_off
                      }
        }

        self.fade_pause = 40  # ms
        self.vt.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'],  self.hm_dict['dusk'])
        self.vt.run_ev.set()  # start the clock

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

    def write_strip_by_state(self, state):
        """ set strip to state colour """
        self.nps.set_strip_rgb(self.state_rgb[state])
        self.nps.write()

    # state-transition methods

    async def set_off(self):
        """ coro: set state 'off' """
        self.write_strip_by_state('off')
        self.fade_flag = False  # stop fade if running
        await asyncio.sleep_ms(self.fade_pause + 10)
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['off'])
        self.state = 'off'

    async def set_day(self):
        """ coro: set state 'day' """
        self.write_strip_by_state('day')
        await asyncio.sleep_ms(20)
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['day'])
        self.state = 'day'

    async def set_night(self):
        """ coro: set state 'night' """
        self.write_strip_by_state('night')
        await asyncio.sleep_ms(20)
        self.lcd.write_line(0, self.lcd_str['state'])
        self.lcd.write_line(1, self.lcd_str['night'])
        self.state = 'night'

    async def set_by_clock(self):
        """ coro: set state 'clock' """
        # end possible existing task
        self.fade_flag = False
        await asyncio.sleep_ms(200)
        self.vt.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'],  self.hm_dict['dusk'])
        self.fade_flag = True
        asyncio.create_task(self.clock_transitions())
        self.state = 'clock'

    async def no_t(self):
        """ coro: no transition """
        await asyncio.sleep_ms(20)
        return self.state

    # transition methods

    async def state_transition_logic(self, btn_state):
        """ coro: invoke transition for state & button-press event """
        transitions = self.transitions[self.state]
        if btn_state in transitions:
            await transitions[btn_state]()  # invoke transition method
        await asyncio.sleep_ms(20)  # allow scheduler to run tasks

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """ coro: fade transition """

            async def do_fade(state_0_, state_1_):
                """ coro: do the fade """
                h_0, s_0, v_0 = self.state_hsv[state_0_]
                d_h = (self.state_hsv[state_1_][0] - h_0) / 100
                d_s = (self.state_hsv[state_1_][1] - s_0) / 100
                d_v = (self.state_hsv[state_1_][2] - v_0) / 100
                i = 0
                while i < 100 and self.fade_flag:
                    rgb = self.cs.rgb_g(self.cs.hsv_rgb((h_0, s_0, v_0)))
                    self.nps.set_strip_rgb(rgb)
                    self.nps.write()
                    await asyncio.sleep_ms(self.fade_pause)
                    h_0 += d_h
                    s_0 += d_s
                    v_0 += d_v
                    i += 1
                # ensure target state is set
                if self.fade_flag:
                    self.write_strip_by_state(state_1_)
                    await asyncio.sleep_ms(1)

            # fade in 2 steps via red sunset/sunrise
            print(f'Start fade from {state_0}')
            await do_fade(state_0, 'mid')
            await do_fade('mid', state_1)
            print(f'End   fade from {state_0}')

        # clock_transitions
        # clear any previous Event setting; initialise state
        self.vt.change_state_ev.clear()
        day_night_state = self.vt.state
        self.write_strip_by_state(day_night_state)
        await asyncio.sleep_ms(1)
        # fade rgb between states
        while self.fade_flag:  # cleared if OFF or restart pressed
            await self.vt.change_state_ev.wait()
            if day_night_state == 'day':
                target_state = 'night'
            else:
                target_state = 'day'
            # consumer must clear Event
            self.vt.change_state_ev.clear()
            await fade(day_night_state, target_state)
            await asyncio.sleep_ms(20)
            day_night_state = target_state


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def holding_task():
        """ coro: run forever """
        while True:
            await asyncio.sleep_ms(1_000)

    async def process_event(btn, system_):
        """ coro: passes button events to the system """
        while True:
            await btn.press_ev.wait()
            await system_.state_transition_logic(btn.state)
            btn.clear_state()

    async def show_time(vt_, lcd_):
        """ coro: print virtual time every 1s in 'clock' state """
        day_str = 'day'.center(16)
        night_str = 'night'.center(16)
        day_marker = vt_.get_day_marker()
        night_marker = vt_.get_night_marker()
        while True:
            await vt_.minute_ev.wait()
            vt_.minute_ev.clear()
            if system.state == 'clock':
                m = vt_.get_clock_m()
                time_str = vt_.get_time_hm().center(16)
                if day_marker <= m < night_marker:
                    p_str = day_str
                else:
                    p_str = night_str

                lcd_.write_line(0, time_str)
                lcd_.write_line(1, p_str)
                gc.collect()

    # ====== parameters

    n_pixels = 64

    # state colours as HSV
    state_hsv = {
        'day': (240 / 360, 0.1, 0.95),
        'night': (359 / 360, 0.0, 0.15),
        'mid': (359 / 360, 1.0, 0.5),
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
    vt = VTime(t_mpy=clock_speed)  # fast virtual clock
    system = DayNightST(cs, nps, vt, lcd, hsv=state_hsv, hm=clock_hm)
    # initialise
    board.set_onboard((0, 15, 0))  # on
    lcd.initialise()  # show state when set
    await system.set_off()
    print('System initialised')

    # create tasks respond to events
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # buttons self-poll
        asyncio.create_task(process_event(buttons[b], system))  # respond to event
    asyncio.create_task(show_time(system.vt, lcd))
    
    await holding_task()

    system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
