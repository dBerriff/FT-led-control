# v_time.py
""" cut-down virtual time class to support lighting control """

import asyncio
from micropython import const


class VTime:
    """
        implement virtual (fast) time
        - include methods to handle day-night change of state
    """
    S_IN_DAY = const(3600 * 24)

    def __init__(self, s_inc):
        self.s_inc = s_inc
        self._vt_s = 0
        self._sunrise = 0
        self._sunset = 0
        self.state = None
        self.run_ev = asyncio.Event()
        self.change_state_ev = asyncio.Event()

    def get_day_s(self):
        """ return virtual seconds since midnight """
        return self._vt_s

    def get_time_hm(self):
        """ return virtual time as str 'hh:mm' """
        return f'{self._vt_s // 3600:02d}:{self._vt_s // 60 % 60:02d}'

    async def track_transitions(self):
        """ check time against _sunrise and _sunset """
        while self.run_ev.is_set():
            t = self._vt_s
            if self._sunrise <= t < self._sunset:
                state = 'day'
            else:
                state = 'night'
            if state != self.state:
                self.change_state_ev.set()
                self.state = state
            await asyncio.sleep_ms(1_000)

    async def tick(self):
        """ run virtual clock; update every RTC s """
        inc = self.s_inc  # avoid repeated dict lookup
        while self.run_ev.is_set():
            await asyncio.sleep_ms(1000)
            self._vt_s += inc
            self._vt_s %= self.S_IN_DAY

    def start_clock(self, time_hm, sunrise, sunset):
        """ create tasks to run virtual time """
        self._vt_s = self.calc_day_s(time_hm)
        self._sunrise = self.calc_day_s(sunrise)
        self._sunset = self.calc_day_s(sunset)
        self.run_ev.set()
        asyncio.create_task(self.tick())
        asyncio.create_task(self.track_transitions())

    @staticmethod
    def calc_day_s(h_m):
        """ calculate seconds since midnight from hh:mm string """
        h_m = h_m.strip()
        h_m = h_m.split(':')
        return int(h_m[0]) * 3600 + int(h_m[1]) * 60

    def __str__(self):
        return f'{self.get_time_hm()} {self.state}  '


async def main():
    """ test VTime class """

    async def show_time(vt_):
        """ print virtual time at set intervals """
        while True:
            print(vt_, end='\r')
            await asyncio.sleep_ms(1_000)

    async def show_state(vt_):
        """ respond to and clear change-of-_state Event """
        while True:
            await vt_.change_state_ev.wait()
            print(f'Change state to: {vt_.state}')
            vt_.change_state_ev.clear()

    vt = VTime(s_inc=3600)
    await asyncio.sleep(5)
    vt.start_clock(time_hm='12:00', sunrise='06:00', sunset='20:00')
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
