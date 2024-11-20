# lighting_states.py

# state-transition logic
"""
self.transitions = {
    'off': {'A1': self.set_day,
            'B1': self.set_by_clock,
            'U1': self.no_t},
    'day': {'A1': self.set_night,
            'B1': self.no_t,
            'U2': self.set_off},
    'night': {'A1': self.set_day,
              'B1': self.no_t,
              'U2': self.set_off},
    'clock': {'A1': self.no_t,
              'B1': self.no_t,
              'B2': self.set_by_clock,
              'U2': self.set_off
              }
"""

import asyncio

from config import write_cf
from lighting_state import LightingState


class Off(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'


class Start(LightingState):
    """
        null state to get started
        - immediately transitions to Stopped
    """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'

    async def state_enter(self):
        """ auto trigger to next state """
        print(f'Enter state: {self.name}')
        asyncio.create_task(self.system.transition(self.transitions['auto']))


class Day(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'



class Night(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'



class Clock(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'


