# lighting_state.py

""" abstract state class for system states """

import asyncio


class LightingState:
    """
        Abstract Base Class for lighting states; system: LightingSystem is context
        - each concrete state:
            -- defines its associated events and response methods
            -- system.state_lock waits for any previous state task to complete
            -- system.transition_lock prevents concurrent transitions
    """

    def __init__(self, system):
        self.system = system
        self.buffer = system.buffer
        self.btn_lock = system.btn_lock
        self.lcd = system.lcd
        self.name = 'abstract base'
        self.transitions = dict()  # loaded from dict definitions in InclineSystem
        self.remain = True
        self.run_flag = False

    async def state_enter(self):
        """ on state entry """
        print(f'Enter state: {self.name}')
        await self.system.lcd.write_display(f'{self.name:<16}', f'{" ":<16}')
        self.remain = True  # in state: flag for while loops
        await self.schedule_tasks()

    async def schedule_tasks(self):
        """ load state tasks to run sequentially or concurrently (default) """
        # await self.state_task()
        # await self.transition_trigger()
        await asyncio.gather(self.state_task(), self.transition_trigger())

    async def state_task(self):
        """ run while in state """
        async with self.system.state_lock:
            pass

    async def transition_trigger(self):
        """ wait for buffer event """
        async with self.system.transition_lock:
            while True:
                await self.buffer.is_data.wait()
                # block button inputs until response complete
                async with self.btn_lock:
                    ev_tuple = await self.buffer.get()
                    ev = ev_tuple[0] + ev_tuple[1]
                    print(ev)
                    if ev in self.transitions:
                        self.remain = False
                        asyncio.create_task(self.system.transition(self.transitions[ev]))
                        break
                    else:
                        print(f'Event {ev} ignored')

    async def state_exit(self):
        """ on state exit """
        self.remain = False
        # allow looped tasks to end
        await asyncio.sleep_ms(20)
        self.system.prev_state_name = str(self.name)

