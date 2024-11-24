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
            self.system.clear_strip()
            await asyncio.sleep_ms(2)


class Day(LightingState):
    """ state: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Day'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            self.set_strip_rgb(self.state_rgb['Day'])
            self.write_strip()
            self.lcd.write_display(self.system.lcd_str['state'],
                                   self.system.lcd_str[self.name])


class Night(LightingState):
    """ state: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Night'

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            self.set_strip_rgb(self.state_rgb['Night'])
            self.write_strip()
            self.lcd.write_display(self.system.lcd_str['state'],
                                   self.system.lcd_str[self.name])


class ClockDay(LightingState):
    """
        set state to Day under clock control
        - state Off transitions to this state on B1 event
    """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'ClockDay'
        self.state_hsv = self.system.phase_hsv
        self.dawn = self.system.phase_m['dawn_m']
        self.dusk = self.system.phase_m['dusk_m']

    async def state_enter(self):
        """ on state entry """
        print(f'Enter state: {self.name}')
        await self.system.lcd.write_display(f'{self.name:<16}', f'{" ":<16}')
        self.remain = True  # in state: flag for while loops
        await self.schedule_tasks()

    async def state_task(self):
        """ run while in state """
        # if it is Day, set as Day, else transition to Night
        if self.dawn <= self.system.v_minutes < self.dusk:  # Day
            async with self.system.state_lock:
                await self.do_fade('Night', 'Mid')
                await self.do_fade('Mid', 'Day')
        else:  # Night
            await self.buffer.put('T1')


class ClockNight(LightingState):
    """ set state to Night under clock control """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'ClockNight'
        self.state_hsv = self.system.phase_hsv

    async def state_enter(self):
        """ on state entry """
        print(f'Enter state: {self.name}')
        await self.system.lcd.write_display(f'{self.name:<16}', f'{" ":<16}')
        self.remain = True  # in state: flag for while loops
        await self.schedule_tasks()

    async def state_task(self):
        """ run while in state """
        # can only transition here from Day
        async with self.system.state_lock:
            await self.do_fade('Day', 'Mid')
            await self.do_fade('Mid', 'Night')


class Finish(LightingState):
    """ state: finish execution """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Finish'

    async def schedule_tasks(self):
        """ load state tasks to run sequentially """
        await self.state_task()
        # no further transitions

    async def state_task(self):
        """ flag completes system.run_system task """
        self.system.run = False
        asyncio.sleep_ms(200)
