# v_time.py
""" cut-down virtual time class to support lighting control """

import asyncio
from micropython import const


class VTime:
    """
        implement virtual (fast) time
        - include methods to handle day-night change of state
        - Event change_state_ev flags dawn or dusk
    """
    S_IN_DAY = const(3600 * 24)

    def __init__(self, s_inc):
        self.s_inc = s_inc
        self._vt_s = 0
        self._dawn = 0
        self._dusk = 0
        self.state = None
        self.run_ev = asyncio.Event()
        self.change_state_ev = asyncio.Event()
        asyncio.create_task(self.tick())

    def get_clock_s(self):
        """ return virtual seconds since midnight """
        return self._vt_s

    def get_day_marker(self):
        """ return start of day """
        return self._dawn

    def get_night_marker(self):
        """ return start of night """
        return self._dusk

    def get_time_hm(self):
        """ return virtual time as str 'hh:mm' """
        return f'{self._vt_s // 3600:02d}:{self._vt_s // 60 % 60:02d}'

    async def tick(self):
        """ run virtual clock; update every RTC s """
        inc = self.s_inc  # avoid repeated dict lookup
        while True:
            await asyncio.sleep_ms(1000)
            await self.run_ev.wait()
            self._vt_s += inc
            self._vt_s %= self.S_IN_DAY
            t = self._vt_s
            if self._dawn <= t < self._dusk:
                state = 'day'
            else:
                state = 'night'
            if state != self.state:
                self.change_state_ev.set()
                self.state = state

    def init_clock(self, start_time_hm_, sunrise_hm_, sunset_hm_):
        """ virtual clock """
        self._vt_s = self.get_hm_s(start_time_hm_)
        self._dawn = self.get_hm_s(sunrise_hm_)
        self._dusk = self.get_hm_s(sunset_hm_)
        if self._dawn <= self._vt_s < self._dusk:
            self.state = 'day'
        else:
            self.state = 'night'

    def __str__(self):
        return f'{self.get_time_hm()} {self.state}  '

    @staticmethod
    def get_hm_s(hm_):
        """ convert time in hh:mm to seconds-since-midnight """
        h_m_tokens = hm_.split(':')
        return int(h_m_tokens[0]) * 3600 + int(h_m_tokens[1]) * 60


async def main():
    """ test VTime class """

    async def show_time(vt_):
        """ print virtual time at set intervals """
        while True:
            print(vt_, end='\r')
            await asyncio.sleep_ms(1_000)

    async def show_state(vt_):
        """ respond to and clear change-of-state Event """
        while True:
            await vt_.change_state_ev.wait()
            print(f'Change state to: {vt_.state}')
            vt_.change_state_ev.clear()

    vt = VTime(s_inc=720)
    vt.init_clock('12:00', '06:00', '20:00')
    vt.run_ev.set()  # start the clock
    asyncio.create_task(show_time(vt))
    asyncio.create_task(show_state(vt))    
    await asyncio.sleep(20)
    # stop the clock
    vt.run_ev.clear()
    await asyncio.sleep(10)
    # resume
    vt.run_ev.set()
    await asyncio.sleep(60)
    vt.run_ev.clear()
    await asyncio.sleep_ms(20)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
