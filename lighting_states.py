# lighting_states.py

import asyncio

from lighting_state import LightingState


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


class Off(LightingState):
    """ state: lighting off, waiting for button input """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Off'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            await asyncio.sleep_ms(2)


class Day(LightingState):
    """ state: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Day'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            await self.system.write_strip_by_state(self.name)
            self.lcd.write_display(self.system.lcd_str_dict['state'],
                                   self.system.lcd_str_dict[self.name])


class Night(LightingState):
    """ state: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Night'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            await self.system.write_strip_by_state(self.name)
            self.lcd.write_display(self.system.lcd_str_dict['state'],
                                   self.system.lcd_str_dict[self.name])


class Clock(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Clock'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            await self.system.write_strip_by_state(self.name)
            self.lcd.write_display(self.system.lcd_str_dict['state'],
                                   self.system.lcd_str_dict[self.name])
