# v_time.py
""" cut-down virtual time class to support lighting control """

import asyncio
from collections import namedtuple
from micropython import const

Vms = namedtuple('Vms', ('hr', 'min'))


class VTime:
    """ implement virtual (fast) time """

    s_in_day = const(3600 * 24)
    
    def __init__(self, s_inc=72):
        self.s_inc = s_inc
        self._t_s = 0

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

    async def v_tick(self):
        """ run virtual clock """
        inc = self.s_inc  # avoid repeated dict lookup
        while True:
            await asyncio.sleep_ms(1000)
            self._t_s += inc
            self._t_s %= self.s_in_day

    def get_time(self):
        """ return virtual time (h, m) """
        return Vms(self.h, self.m)


async def main():
    """ test HMSTime class """

    async def show_time(v_time):
        """"""
        while True:
            t = v_time.get_time()
            print(f'{t.hr}h:{t.min}m')
            await asyncio.sleep_ms(1000)

    vt = VTime(72)
    asyncio.create_task(vt.v_tick())
    await asyncio.sleep_ms(0)  # enable task start
    await show_time(vt)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('Execution complete')
