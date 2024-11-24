# lighting_state_transition.py
""" model ambient light state transitions """

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
        - call run_system to start
    """

    VERSION = const('FT Lighting v1.0')

    # class default parameters: kwargs can override
    # phase colours as HSV
    phase_hsv = {
        'Day': (240.0, 0.1, 0.95),
        'Night': (359.0, 0.0, 0.15),
        'Mid': (359.0, 1.0, 0.5),
        'Off': (0.0, 0.0, 0.0)
    }
    # phase transition times
    phase_hm = {'dawn': '06:00', 'dusk': '20:30', 'start': '12:00'}
    t_mpy = 72  # clock-speed multiplier
    # strings for LCD
    lcd_str = {
        'blank': ''.center(16),
        'state': 'State'.center(16),
        'Off': 'off'.center(16),
        'Day': 'day'.center(16),
        'Night': 'night'.center(16),
        'ClockDay': 'clock day'.center(16),
        'ClockNight': 'clock night'.center(16)
    }

    def __init__(self, board_, pxl_drv_, lcd_, **kwargs):
        self.board = board_
        self.pxl_drv = pxl_drv_
        self.lcd = lcd_
        # override defaults with kwargs if any
        if 'phase_hsv' in kwargs:
            self.phase_hsv = kwargs['phase_hsv']
        else:
            self.phase_hsv = LightingSystem.phase_hsv
        if 'hm' in kwargs:
            self.phase_hm = kwargs['hm']
        else:
            self.phase_hm = LightingSystem.phase_hm
        if 'lcd_str' in kwargs:
            self.lcd_str = kwargs['lcd_str']
        else:
            self.lcd_str = LightingSystem.lcd_str
        if 't_mpy' in kwargs:
            self.t_mpy = kwargs['t_mpy']
        else:
            self.t_mpy = LightingSystem.t_mpy

        self.v_clock = VClock(self.t_mpy)
        self.v_minutes = None  # since midnight
        self.minute_ev = self.v_clock.minute_ev
        self.phase_m = {'dawn_m': conv_vt_m(self.phase_hm['dawn']),
                        'dusk_m': conv_vt_m(self.phase_hm['dusk'])
                        }
        self.phase_ev = asyncio.Event()
        self.phase = 'None'
        self.phase_hsv = LightingSystem.phase_hsv

        self.clr_space = ColourSpace()
        self.state_rgb = {}

        # build RGB dict for state colours
        for key in self.phase_hsv:
            self.state_rgb[key] = self.clr_space.rgb_g(
                self.clr_space.hsv_rgb(self.phase_hsv[key]))

        button_set = tuple([Button(self.board.buttons['A'], 'A'),
                            HoldButton(self.board.buttons['B'], 'B'),
                            HoldButton(self.board.buttons['U'], 'U')])
        self.buffer = Buffer()
        self.button_group = ButtonGroup(button_set, self.buffer)

        # no concurrent states or transitions allowed
        # locks enforce the rules. but might not be required if sequence does that
        # btn_lock: required to ignore button events (lock out external demands)
        self.state_lock = asyncio.Lock()
        self.transition_lock = asyncio.Lock()
        self.btn_lock = self.button_group.btn_lock

        # aliases
        self.set_strip_rgb = self.pxl_drv.set_strip_rgb
        self.clear_strip = self.pxl_drv.clear_strip
        self.write_strip = self.pxl_drv.write

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
                                  'B1': self.clock_day_s,
                                  'U2': self.finish_s}
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

        # start the system
        self.v_clock.init_v_time(conv_vt_m(self.phase_hm['start']))
        self.state = self.start_s
        # cannot await in init
        asyncio.create_task((self.time_triggers()))
        self.button_group.poll_buttons()  # activate button self-polling
        self.run = True

    async def run_system(self):
        """ this coro is awaited while system is running """
        await self.state.state_enter()
        while self.run:
            await asyncio.sleep_ms(200)


    async def time_triggers(self):
        """ set time triggers """
        dawn_m = int(self.phase_m['dawn_m'])
        dusk_m = int(self.phase_m['dusk_m'])
        # wait for clock tick then initialise
        await self.minute_ev.wait()
        self.v_clock.minute_ev.clear()
        self.v_minutes = self.v_clock.v_minutes
        while True:
            await self.minute_ev.wait()
            self.v_clock.minute_ev.clear()  # should not need to be cleared elsewhere
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
            self.state = new_state
            gc.collect()
            asyncio.create_task(self.state.state_enter())


async def main():
    """ coro: initialise then run tasks under asyncio scheduler """

    # ====== parameters
    n_pixels = 119 + 119
    t_mpy = 72
    # ====== end-of-parameters

    # instantiate system objects
    board = DriverBoard()
    driver = Ws2812(board.strip_pins['dat'])
    nps = PixelStrip(driver, n_pixels)
    lcd = LcdApi(board.i2c_pins)
    system = LightingSystem(board, nps, lcd, t_mpy=t_mpy)

    # initialise
    board.set_onboard((0, 1, 0))  # on
    print('System initialised')

    # run the system
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
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
