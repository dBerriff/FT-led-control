# v_time.py
""" cut-down virtual time class to support lighting control """

import asyncio
from collections import namedtuple
from micropython import const


class VTime:
    """
        implement virtual (fast) time
        - include methods to handle day-night change of state
    """
    Vhm = namedtuple('Vhm', ('hr', 'min'))
    s_in_day = const(3600 * 24)
    
    def __init__(self, s_inc=72, time=Vhm(hr=12, min=0)):
        self.s_inc = s_inc
        self._t_s = time.hr * 3600 + time.min * 60
        self.state = None
        self.change_state_ev = asyncio.Event()

    @property
    def h(self):
        """ return virtual hour """
        return self._t_s // 3600

    @property
    def m(self):
        """ return virtual minute """
        return self._t_s // 60 % 60

    @property
    def s(self):
        """ return virtual second """
        return self._t_s % 60

    async def tick(self):
        """ run virtual clock """
        inc = self.s_inc  # avoid repeated dict lookup
        while True:
            await asyncio.sleep_ms(1000)
            self._t_s += inc
            self._t_s %= self.s_in_day

    @property
    def time_hm(self):
        """ return virtual time (h, m) """
        return self.Vhm(self.h, self.m)

    @time_hm.setter
    def time_hm(self, time_):
        """ """
        self._t_s = time_.hr * 3600 + time_.min * 60

    async def check_day_transition(self, sunset_=72_000, sunrise_=21_600):
        """"""
        while True:
            t = self.daytime_seconds(self.time_hm)
            state = 'day' if sunrise_ < t < sunset_ else 'night'
            if state != self.state:
                self.state = state
                self.change_state_ev.set()
            await asyncio.sleep_ms(1_000)

    def start_clock(self):
        """ create tasks to run virtual time """
        asyncio.create_task(self.tick())
        asyncio.create_task(self.check_day_transition())

    def __str__(self):
        return f'{self.time_hm}'

    @staticmethod
    def daytime_seconds(time_):
        """ convert hours and minutes to seconds since midnight """
        return time_.hr * 3600 + time_.min * 60


async def main():
    """ test VTime class """

    async def show_time(vt_):
        """ print virtual time at set intervals """
        while True:
            print(vt_)
            await asyncio.sleep_ms(1_000)

    async def show_state(vt_):
        """ respond to and clear change-of-state Event """
        while True:
            await vt_.change_state_ev.wait()
            print(f'Change state to: {vt_.state}')
            vt_.change_state_ev.clear()

    vt = VTime(720)
    vt.start_clock()
    await asyncio.sleep_ms(20)
    asyncio.create_task(show_state(vt))
    await asyncio.sleep_ms(20)
    await show_time(vt)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
