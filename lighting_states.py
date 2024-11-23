# lighting_states.py

import asyncio

from lighting_state import LightingState


class Start(LightingState):
    """
        null phase to get started
        - immediately transitions to Stopped
    """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Start'

    async def state_enter(self):
        """ auto trigger to next phase """
        print(f'Enter phase: {self.name}')
        asyncio.create_task(self.system.transition(self.transitions['auto']))


class Off(LightingState):
    """ phase: lighting off, waiting for button input """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Off'

    async def state_task(self):
        """ run while in phase """
        async with self.system.state_lock:
            self.system.clear_strip()
            await asyncio.sleep_ms(2)


class Day(LightingState):
    """ phase: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Day'

    async def state_task(self):
        """ run while in phase """
        async with self.system.state_lock:
            self.set_strip_rgb(self.state_rgb['Day'])
            self.write_strip()
            self.lcd.write_display(self.system.lcd_str_dict['phase'],
                                   self.system.lcd_str_dict[self.name])


class Night(LightingState):
    """ phase: lighting set to daytime HSV values """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Night'

    async def state_task(self):
        """ run while in phase """
        async with self.system.state_lock:
            self.set_strip_rgb(self.state_rgb['Night'])
            self.write_strip()
            self.lcd.write_display(self.system.lcd_str_dict['phase'],
                                   self.system.lcd_str_dict[self.name])


class ClockDay(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'ClockDay'

    async def state_enter(self):
        """ on phase entry """
        print(f'Enter phase: {self.name}')
        await self.system.lcd.write_display(f'{self.name:<16}', f'{" ":<16}')
        self.remain = True  # in state: flag for while loops
        await self.schedule_tasks()

    async def state_task(self):
        """ run while in phase """
        # check to see if it is day
        if self.system.phase_dict['dawn'] <= self.system.v_minutes < self.system.phase_dict['dusk']:
            async with self.system.state_lock:
                print(f'{self.name}: fade to day...')
                self.set_strip_rgb(self.state_rgb['Day'])
                self.write_strip()
                await asyncio.sleep_ms(1)
                self.lcd.write_display(self.system.lcd_str_dict['Day'],
                                       self.system.lcd_str_dict[self.name])
        else:
            await self.buffer.put('T1')


class ClockNight(LightingState):
    """"""

    def __init__(self, system):
        super().__init__(system)
        self.name = 'ClockNight'

    async def state_enter(self):
        """ on phase entry """
        print(f'Enter phase: {self.name}')
        await self.system.lcd.write_display(f'{self.name:<16}', f'{" ":<16}')
        self.remain = True  # in state: flag for while loops
        await self.schedule_tasks()

    async def state_task(self):
        """ run while in phase """
        async with self.system.state_lock:
            print(f'{self.name}: fade to night...')
            self.set_strip_rgb(self.state_rgb['Night'])
            self.write_strip()
            self.lcd.write_display(self.system.lcd_str_dict['phase'],
                                   self.system.lcd_str_dict[self.name])


class Finish(LightingState):
    """ phase: finish execution """

    def __init__(self, system):
        super().__init__(system)
        self.name = 'Finish'

    async def schedule_tasks(self):
        """ no phase tasks """
        self.system.run = False
        await asyncio.sleep_ms(200)  # for close-down
