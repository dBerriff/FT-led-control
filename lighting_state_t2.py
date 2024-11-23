# lighting_state_transition.py
""" model ambient light phase transitions """

import asyncio
import gc

from colour_space import ColourSpace
from lcd_1602 import LcdApi
from pixel_strip import PixelStrip
from plasma import Plasma2040 as DriverBoard
from v_clock import VClock, conv_vt_m, conv_m_vt
from ws2812 import Ws2812
from lighting_states import Start, Off, Day, Night, ClockDay, ClockNight, Finish
from buttons import Button, HoldButton, ButtonGroup
from queue import Buffer


class LightingSystem:
    """
        lighting State-Transition system
        - context for lighting states
        - dict stores: event: transitions
    """

    VERSION = const('FT Lighting v1.0')

    # phase colours as HSV
    state_hsv = {
        'Day': (240.0, 0.1, 0.95),
        'Night': (359.0, 0.0, 0.15),
        'Mid': (359.0, 1.0, 0.5),
        'Off': (0.0, 0.0, 0.0)
    }
    lcd_str_dict = {
        'blank': ''.center(16),
        'phase': 'State'.center(16),
        'Off': 'off'.center(16),
        'Day': 'day'.center(16),
        'Night': 'night'.center(16),
        'ClockDay': 'clock day'.center(16),
        'ClockNight': 'clock night'.center(16)
    }
    hm_dict = {'hm': '19:30', 'dawn': '06:00', 'dusk': '20:30'}

    def __init__(self, board, nps, lcd_, **kwargs):
        self.board = board
        self.pxl_strip_drv = nps
        self.lcd = lcd_
        self.v_clock = VClock(t_mpy=720)
        self.v_minutes = None  # since midnight
        self.minute_ev = self.v_clock.minute_ev
        self.phase_dict = {'dawn_m': conv_vt_m(self.hm_dict['dawn']),
                           'dusk_m': conv_vt_m(self.hm_dict['dusk'])
                           }
        self.phase_ev = asyncio.Event()
        self.phase = 'None'
        self.clr_space = ColourSpace()
        self.end_fade = True
        self.state_hsv = LightingSystem.state_hsv
        self.state_rgb = {}
        if 'hsv' in kwargs:
            self.build_state_colour_dicts(kwargs['hsv'])
        else:
            self.build_state_colour_dicts(self.state_hsv)
        if 'hm' in kwargs:
            self.hm_dict = kwargs['hm']
        if 'lcd_s' in kwargs:
            self.lcd_str_dict = kwargs['lcd_s']
        button_set = tuple([Button(board.buttons['A'], 'A'),
                            HoldButton(board.buttons['B'], 'B'),
                            HoldButton(board.buttons['U'], 'U')])
        self.buffer = Buffer()
        self.button_group = ButtonGroup(button_set, self.buffer)

        # no concurrent states or transitions allowed
        # locks enforce the rules. but might not be required if sequence does that
        # btn_lock: required to ignore button events (lock out external demands)
        self.state_lock = asyncio.Lock()
        self.transition_lock = asyncio.Lock()
        self.btn_lock = self.button_group.btn_lock

        # aliases
        self.set_strip_rgb = self.pxl_strip_drv.set_strip_rgb
        self.clear_strip = self.pxl_strip_drv.clear_strip
        self.write_strip = self.pxl_strip_drv.write


        # === system states
        self.start_s = Start(self)
        self.off_s = Off(self)
        self.day_s = Day(self)
        self.night_s = Night(self)
        self.clock_day_s = ClockDay(self)
        self.clock_night_s = ClockNight(self)
        self.finish_s = Finish(self)

        # === system transitions
        self.start_s.transitions = {'auto': self.off_s}
        self.off_s.transitions = {'A1': self.day_s,
                                  'B1': self.clock_day_s}
        self.day_s.transitions = {'A1': self.night_s,
                                  'U2': self.off_s}
        self.night_s.transitions = {'A1': self.day_s,
                                    'U2': self.off_s}
        self.clock_day_s.transitions = {'T1': self.clock_night_s,
                                        'U2': self.off_s}
        self.clock_night_s.transitions = {'T0': self.clock_day_s,
                                          'U2': self.off_s}
        self.finish_s.transitions = {'auto': None}
        # ===

        self.prev_state_name = None
        self.state = self.start_s

        # start the system including virtual clock
        self.v_clock.init_v_time(conv_vt_m('12:00'))
        self.phase_dict = {'dawn': conv_vt_m(self.hm_dict['dawn']),
                           'dusk': conv_vt_m(self.hm_dict['dusk'])
                           }
        self.prev_state_name = ''
        self.state = self.start_s
        self.run = True
        asyncio.create_task((self.time_triggers()))
        asyncio.create_task(self.state.state_enter())  # cannot await in init
        self.button_group.poll_buttons()  # activate button self-polling

    async def time_triggers(self):
        """ set time triggers """
        dawn_m = int(self.phase_dict['dawn'])
        dusk_m = int(self.phase_dict['dusk'])
        # wait for clock tick then initialise
        await self.minute_ev.wait()
        self.v_clock.minute_ev.clear()
        self.v_minutes = self.v_clock.v_minutes
        while True:
            await self.minute_ev.wait()
            self.v_clock.minute_ev.clear()
            v_minutes = self.v_clock.v_minutes
            self.lcd.write_line(1, conv_m_vt(v_minutes))
            if v_minutes == dawn_m:
                await self.buffer.put('T0')
            elif v_minutes == dusk_m:
                await self.buffer.put('T1')
            self.v_minutes = v_minutes

    async def transition(self, new_state):
        """ transition from current to new ev_type """
        await self.state.state_exit()
        async with self.transition_lock:
            self.prev_state_name = str(self.state.name)
            self.state = new_state
            gc.collect()
            asyncio.create_task(self.state.state_enter())

    async def run_system(self):
        """ run the system """
        while self.run:
            await asyncio.sleep_ms(20)

    # lighting control methods specific to this context
    # set LED strip display phase
    def build_state_colour_dicts(self, state_hsv_):
        """
            load HSV and RGB dicts with phase as key
            - HSV for day/night transition
            - RGB for static colours
        """
        for key in state_hsv_:
            self.state_hsv[key] = state_hsv_[key]
            self.state_rgb[key] = self.clr_space.rgb_g(self.clr_space.hsv_rgb(state_hsv_[key]))


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    # ====== parameters
    n_pixels = 119 + 119
    # ====== end-of-parameters

    # instantiate system objects
    board = DriverBoard()
    driver = Ws2812(board.strip_pins['dat'])
    nps = PixelStrip(driver, n_pixels)
    lcd = LcdApi(board.i2c_pins)
    system = LightingSystem(board, nps, lcd)

    # initialise
    board.set_onboard((0, 1, 0))  # on
    print('System initialised')

    # create tasks respond to events

    print(f'Running the system: {system.VERSION}')
    try:
        await system.run_system()
    finally:
        print('Closing down the system')

    # await system.set_off()
    await asyncio.sleep_ms(200)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained phase
        print('execution complete')
