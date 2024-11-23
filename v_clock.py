# v_clock.py
""" cut-down virtual time class to support lighting control """

import asyncio
from micropython import const


def conv_vt_m(hm_):
    """ convert time as 'hh:mm' to minutes-since-midnight """
    h_m_tokens = hm_.split(':')
    return int(h_m_tokens[0]) * 60 + int(h_m_tokens[1])


def conv_m_vt(vm_):
    """ convert time as minutes-since-midnight to 'hh:mm' """
    hrs_ = vm_ // 60
    min_ = vm_ - hrs_ * 60
    return f'{hrs_:02d}:{min_:02d}'


class VClock:
    """ Virtual (fast) time as minutes since midnight """

    M_IN_DAY = const(24 * 60)

    def __init__(self, t_mpy=1):
        self.m_ms = 60_000 // t_mpy
        self._vt_m = 0
        self.minute_ev = asyncio.Event()  # virtual minute update
        asyncio.create_task(self.tick())

    @property
    def v_minutes(self):
        """ return virtual minutes since midnight """
        return self._vt_m

    def init_v_time(self, vt_m_):
        """ initialise virtual time """
        self._vt_m = vt_m_

    async def tick(self):
        """ run virtual clock at 1 tick/virtual-minute
            - v-minute duration specified in ms
        """
        sleep_m_ms = self.m_ms
        while True:
            await asyncio.sleep_ms(sleep_m_ms)
            self._vt_m += 1
            if self._vt_m == self.M_IN_DAY:
                self._vt_m = 0
            self.minute_ev.set()
