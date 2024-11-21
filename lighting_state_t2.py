# lighting_state_transition.py
""" model ambient light state transitions """

import asyncio
import gc
from colour_space import ColourSpace
from lcd_1602 import LcdApi
from pixel_strip import PixelStrip
from plasma import Plasma2040 as DriverBoard
from v_time import VTime
from ws2812 import Ws2812
from lighting_states import Start, Off, Day, Night, Clock
from buttons import Button, HoldButton, ButtonGroup


class LightingSystem:
    """
        lighting State-Transition system
        - context for lighting states
        - dict stores: event: transitions
    """

    VERSION = const('FT Lighting v1.0')
    
    lcd_str_dict = {
        'blank': ''.center(16),
        'state': 'State'.center(16),
        'Off': 'off'.center(16),
        'Day': 'day'.center(16),
        'Night': 'night'.center(16),
        'Clock': 'clock'.center(16)
        }


    def __init__(self, cs, board, nps, vt, lcd_, **kwargs):
        self.clr_space = cs
        self.board = board
        self.pxl_strip_drv = nps
        self.v_time = vt
        self.lcd = lcd_
        self.end_fade = True
        self.state_hsv = {}
        self.state_rgb = {}
        if 'hsv' in kwargs:
            self.build_state_colour_dicts(kwargs['hsv'])
        if 'hm' in kwargs:
            self.hm_dict = kwargs['hm']
        else:
            self.hm_dict = dict()
        if 'lcd_s' in kwargs:
            self.lcd_str_dict = kwargs['lcd_s']
        button_set = tuple([Button(board.buttons['A'], 'A'),
                            HoldButton(board.buttons['B'], 'B'),
                            HoldButton(board.buttons['U'], 'U')])
        self.button_group = ButtonGroup(button_set)
        # no concurrent states or transitions allowed
        # locks enforce the rules. but might not be required if sequence does that
        # btn_lock: required to ignore button events (lock out external demands)
        self.state_lock = asyncio.Lock()
        self.transition_lock = asyncio.Lock()
        self.btn_lock = self.button_group.btn_lock
        self.buffer = self.button_group.buffer  # button event input


        # === system states
        self.start_s = Start(self)
        self.off_s = Off(self)
        self.day_s = Day(self)
        self.night_s = Night(self)
        self.clock_s = Clock(self)

        # === system transitions
        self.start_s.transitions = {'auto': self.off_s}
        self.off_s.transitions =  {'A1': self.day_s,
                                   'B1': self.clock_s}
        self.day_s.transitions = {'A1': self.night_s,
                                  'U2': self.off_s}
        self.night_s.transitions = {'A1': self.day_s,
                                    'U2': self.off_s}
        self.clock_s.transitions = {'B2': self.clock_s,
                                    'U2': self.off_s}
        # ===

        self.prev_state_name = None
        self.state = self.start_s
        self.fade_steps = 1000
        self.fade_pause = 20 * vt.m_interval // self.fade_steps  # over 20 v min
        self.v_time.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'],  self.hm_dict['dusk'])

        # start the system
        self.prev_state_name = ''
        self.state = self.start_s
        self.run = True
        asyncio.create_task(self.state.state_enter())  # cannot await in init
        self.button_group.poll_buttons()  # activate button self-polling


    # set LED strip display state
    def build_state_colour_dicts(self, state_hsv_):
        """
            load HSV and RGB dicts with state as key
            - HSV for day/night transition
            - RGB for static colours
        """
        for key in state_hsv_:
            self.state_hsv[key] = state_hsv_[key]
            self.state_rgb[key] = self.clr_space.rgb_g(self.clr_space.hsv_rgb(state_hsv_[key]))

    async def write_strip_by_state(self, state):
        """ set strip to state colour """
        self.pxl_strip_drv.set_strip_rgb(self.state_rgb[state])
        self.pxl_strip_drv.write()
        await asyncio.sleep_ms(1)

    async def transition(self, new_state):
        """ transition from current to new ev_type """
        await self.state.state_exit()
        async with self.transition_lock:
            self.prev_state_name = str(self.state.name)
            self.state = new_state
            gc.collect()
            # print(f'Free memory: {gc.mem_free()}')
            asyncio.create_task(self.state.state_enter())

    async def run_system(self):
        """ run the system """
        while self.run:
            await asyncio.sleep_ms(20)


# state-transition methods

    async def set_off(self):
        """ coro: set state 'off' """
        # end possible existing tasks
        self.end_fade = True
        self.v_time.change_state_ev.set()
        await asyncio.sleep_ms(self.fade_pause)

        self.v_time.change_state_ev.clear()
        await self.write_strip_by_state('off')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['off'])
        self.state = 'off'

    async def set_day(self):
        """ coro: set state 'day' """
        await self.write_strip_by_state('day')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['day'])
        self.state = 'day'

    async def set_night(self):
        """ coro: set state 'night' """
        await self.write_strip_by_state('night')
        self.lcd.write_line(0, self.lcd_str_dict['state'])
        self.lcd.write_line(1, self.lcd_str_dict['night'])
        self.state = 'night'

    async def set_by_clock(self):
        """ coro: set state 'clock' """
        # end possible existing tasks
        self.end_fade = True
        self.v_time.change_state_ev.set()
        await asyncio.sleep_ms(self.fade_pause)

        self.v_time.change_state_ev.clear()
        self.v_time.init_clock(
            self.hm_dict['hm'], self.hm_dict['dawn'],  self.hm_dict['dusk'])
        self.end_fade = False
        asyncio.create_task(self.clock_transitions())
        self.state = 'clock'

    @staticmethod
    async def no_t():
        """ coro: no transition """
        await asyncio.sleep_ms(1)

    # transition methods

    async def clock_transitions(self):
        """ coro: set output by virtual clock time """

        async def fade(state_0, state_1):
            """ coro: fade transition """

            async def do_fade(state_0_, state_1_):
                """ coro: do the fade """
                steps = self.fade_steps // 2
                h_0, s_0, v_0 = self.state_hsv[state_0_]
                d_h = (self.state_hsv[state_1_][0] - h_0) / steps
                d_s = (self.state_hsv[state_1_][1] - s_0) / steps
                d_v = (self.state_hsv[state_1_][2] - v_0) / steps
                i = 0
                while i < steps:
                    if self.end_fade:
                        break
                    rgb = self.clr_space.rgb_g(self.clr_space.hsv_rgb((h_0, s_0, v_0)))
                    self.pxl_strip_drv.set_strip_rgb(rgb)
                    self.pxl_strip_drv.write()
                    await asyncio.sleep_ms(self.fade_pause)
                    h_0 += d_h
                    s_0 += d_s
                    v_0 += d_v
                    i += 1
                # ensure target state is set
                await self.write_strip_by_state(state_1_)

            # fade in 2 steps via red sunset/sunrise
            print(f'Fade from {state_0}')
            await do_fade(state_0, 'mid')
            await do_fade('mid', state_1)

        # clock_transitions
        day_night = self.v_time.state
        await self.write_strip_by_state(day_night)
        # fade rgb between states
        while not self.end_fade:
            await self.v_time.change_state_ev.wait()
            self.v_time.change_state_ev.clear()
            if self.end_fade:
                break
            if day_night == 'day':
                target_state = 'night'
            else:
                target_state = 'day'
            await fade(day_night, target_state)
            day_night = target_state


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    async def show_time(vt_, lcd_, lcd_s):
        """ coro: print virtual time every 1s in 'clock' state """
        line_len = const(16)
        day_marker = vt_.get_day_marker()
        night_marker = vt_.get_night_marker()
        while True:
            await vt_.minute_ev.wait()
            vt_.minute_ev.clear()
            if system.state == 'clock':
                m = vt_.get_clock_m()
                time_str = vt_.get_time_hm().center(line_len)
                if day_marker <= m < night_marker:
                    p_str = lcd_s['day']
                else:
                    p_str = lcd_s['night']

                lcd_.write_line(0, time_str)
                lcd_.write_line(1, p_str)
                gc.collect()  # garbage collection

    # ====== parameters

    n_pixels = 119 + 119

    # state colours as HSV
    state_hsv = {
        'Day': (240.0, 0.1, 0.95),
        'Night': (359.0, 0.0, 0.15),
        'Mid': (359.0, 1.0, 0.5),
        'Off': (0.0, 0.0, 0.0)
    }

    clock_hm = {'hm': '19:30', 'dawn': '06:00', 'dusk': '20:00'}
    clock_speed = 720

    # for 16-char lines
    lcd_strings = {
        'blank': ''.center(16),
        'state': 'State'.center(16),
        'Off': 'off'.center(16),
        'Day': 'day'.center(16),
        'Night': 'night'.center(16),
        'Clock': 'clock'.center(16)
    }

    # ====== end-of-parameters

    # instantiate system objects
    cs = ColourSpace()
    board = DriverBoard()
    driver = Ws2812(board.strip_pins['dat'])
    nps = PixelStrip(driver, n_pixels)
    lcd = LcdApi({"sda": 0, "scl": 1})
    vt = VTime(t_mpy=clock_speed)  # fast virtual clock
    system = LightingSystem(cs, board, nps, vt, lcd, hsv=state_hsv, hm=clock_hm, lcd_s=lcd_strings)

    # initialise
    board.set_onboard((0, 1, 0))  # on
    print('System initialised')

    # create tasks respond to events

    print(f'Running the system: {system.VERSION}')
    try:
        await system.run_system()
    finally:
        print('Closing down the system')

    await system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
