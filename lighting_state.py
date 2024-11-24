# lighting_state.py

""" abstract state class for system states """

import asyncio
from colour_space import ColourSpace


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
        self.name = 'abstract base'
        self.cs = ColourSpace()
        # aliases
        self.buffer = system.buffer
        self.m_ms = self.system.v_clock.m_ms
        self.btn_lock = system.btn_lock
        self.state_rgb = system.state_rgb
        self.phase_hsv = system.phase_hsv
        self.lcd = system.lcd
        self.set_strip_rgb = self.system.set_strip_rgb
        self.write_strip = self.system.write_strip

        self.transitions = dict()  # loaded from dict definitions in InclineSystem
        self.remain = True

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
        """
            wait for trigger event then respond or ignore
            - print() messages for testing
        """
        async with self.system.transition_lock:
            while True:
                await self.buffer.is_data.wait()
                # block button inputs until response complete
                async with self.btn_lock:
                    trigger_ev = await self.buffer.get()
                    print(f'Event: {trigger_ev}')
                    if trigger_ev in self.transitions:
                        self.remain = False
                        asyncio.create_task(self.system.transition(self.transitions[trigger_ev]))
                        break

    async def state_exit(self):
        """ on state exit """
        self.remain = False  # flag to end while loops
        await asyncio.sleep_ms(20)  # allow looped tasks to end

    # === support methods
    
    async def do_fade(self, phase_0_, phase_1_):
        """ coro: fade light between phases """
        fade_v_minutes = 20
        smoothing = 5
        steps = fade_v_minutes * smoothing
        step_ms = self.m_ms // smoothing
        print(f'{self.name}: fade to {phase_1_}...')
        nps = self.system.pxl_drv
        h_0, s_0, v_0 = self.phase_hsv[phase_0_]
        d_h = (self.phase_hsv[phase_1_][0] - h_0) / steps
        d_s = (self.phase_hsv[phase_1_][1] - s_0) / steps
        d_v = (self.phase_hsv[phase_1_][2] - v_0) / steps
        while steps and self.remain:
            rgb = self.cs.rgb_g(self.cs.hsv_rgb((h_0, s_0, v_0)))
            nps.set_strip_rgb(rgb)
            nps.write()
            await asyncio.sleep_ms(step_ms)
            h_0 += d_h
            s_0 += d_s
            v_0 += d_v
            steps -= 1
        # ensure target phase is set
        self.set_strip_rgb(self.state_rgb[phase_1_])
        self.write_strip()
        await asyncio.sleep_ms(1)
