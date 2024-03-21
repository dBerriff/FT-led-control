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
    S_IN_DAY = const(3600 * 24)
    
    def __init__(self, s_inc=720):
        self.s_inc = s_inc
        self._dt_s = 0
        self.state = None
        self.run_ev = asyncio.Event()
        self.change_state_ev = asyncio.Event()

    @property
    def h(self):
        """ return virtual hour """
        return self._dt_s // 3600

    @property
    def m(self):
        """ return virtual minute """
        return self._dt_s // 60 % 60

    @property
    def s(self):
        """ return virtual seconds since midnight """
        return self._dt_s

    @property
    def time_hm(self):
        """ return virtual time (h, m) """
        return self.Vhm(self.h, self.m)

    @time_hm.setter
    def time_hm(self, time_):
        """ """
        self._dt_s = time_.hr * 3600 + time_.min * 60

    async def check_day_transition(self, sunrise_, sunset_):
        """ check time against sunrise and sunset """
        sunrise_s = sunrise_.hr * 3600 + sunrise_.min * 60
        sunset_s = sunset_.hr * 3600 + sunset_.min * 60
        while self.run_ev.is_set():
            t = self._dt_s
            state = 'day' if sunrise_s < t < sunset_s else 'night'
            if state != self.state:
                self.state = state
                self.change_state_ev.set()
            await asyncio.sleep_ms(1_000)

    async def tick(self):
        """ run virtual clock; update every RTC s """
        inc = self.s_inc  # avoid repeated dict lookup
        while self.run_ev.is_set():
            await asyncio.sleep_ms(1000)
            self._dt_s += inc
            self._dt_s %= self.S_IN_DAY

    def start_clock(self, time_, sunrise, sunset):
        """ create tasks to run virtual time """
        self._dt_s = time_.hr * 3600 + time_.min * 60
        self.run_ev.set()
        asyncio.create_task(self.tick())
        asyncio.create_task(self.check_day_transition(sunrise, sunset))

    def __str__(self):
        return f'{self.time_hm}'


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

    vt = VTime()
    vhm = vt.Vhm
    await asyncio.sleep(5)
    vt.start_clock(
        time_=vhm(12, 0),
        sunrise=vhm(6, 0),
        sunset=vhm(20, 0)
    )
    await asyncio.sleep_ms(20)
    asyncio.create_task(show_state(vt))
    await asyncio.sleep_ms(20)
    
    asyncio.create_task(show_time(vt))
    await asyncio.sleep(120)
    vt.run_ev.clear()
    await asyncio.sleep_ms(20)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
