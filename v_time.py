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
    M_IN_DAY = const(60 * 24)

    def __init__(self, t_mpy):
        self.m_interval = int(60_000 / t_mpy)
        self._vt_m = 0
        self._dawn = 0
        self._dusk = 0
        self.state = None
        self.minute_ev = asyncio.Event()
        self.change_state_ev = asyncio.Event()
        asyncio.create_task(self.tick())

    def get_clock_m(self):
        """ return virtual minutes since midnight """
        return self._vt_m

    def get_day_marker(self):
        """ return start of day """
        return self._dawn

    def get_night_marker(self):
        """ return start of night """
        return self._dusk

    def get_time_hm(self):
        """ return virtual time as str 'hh:mm' """
        return f'{self._vt_m // 60:02d}:{self._vt_m % 60:02d}'

    async def tick(self):
        """ run virtual clock; update every virtual minute """
        wait = self.m_interval  # avoid repeated dict lookup
        while True:
            self.minute_ev.set()
            if self._dawn <= self._vt_m < self._dusk:
                state = 'day'
            else:
                state = 'night'
            if state != self.state:
                self.change_state_ev.set()
                self.state = state
            await asyncio.sleep_ms(wait)
            self._vt_m += 1
            self._vt_m %= self.M_IN_DAY

    def init_clock(self, start_time_hm_, sunrise_hm_, sunset_hm_):
        """ virtual clock """
        self._vt_m = self.get_hm_m(start_time_hm_)
        self._dawn = self.get_hm_m(sunrise_hm_)
        self._dusk = self.get_hm_m(sunset_hm_)
        if self._dawn <= self._vt_m < self._dusk:
            self.state = 'day'
        else:
            self.state = 'night'

    def __str__(self):
        return f'{self.get_time_hm()} {self.state}  '

    @staticmethod
    def get_hm_m(hm_):
        """ convert time in hh:mm to minutes-since-midnight """
        h_m_tokens = hm_.split(':')
        return int(h_m_tokens[0]) * 60 + int(h_m_tokens[1])


async def main():
    """ test VTime class """

    async def show_time(vt_):
        """ print virtual time at set intervals """
        while True:
            await vt_.minute_ev.wait()
            vt_.minute_ev.clear()
            print(vt_, end='\r')

    async def show_state(vt_):
        """ respond to and clear change-of-state Event """
        while True:
            await vt_.change_state_ev.wait()
            print(f'Change state to: {vt_.state}')
            vt_.change_state_ev.clear()

    vt = VTime(t_mpy=1200)
    vt.init_clock('12:00', '06:00', '20:00')
    asyncio.create_task(show_time(vt))
    asyncio.create_task(show_state(vt))    
    await asyncio.sleep(60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
