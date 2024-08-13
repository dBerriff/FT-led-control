# buttons.py
""" implement press and hold buttons
    class Button implements a click button
    class HoldButton extends Button to include a hold event
    - button methods are coroutines
    - create button.poll_state() as a task for a button to self-poll
"""

import asyncio
from machine import Pin, Signal  # Signal class wraps pull-up logic
from micropython import const
from time import ticks_ms, ticks_diff


class Button:
    """ button with click state """
    # button states
    WAIT = const('0')
    CLICK = const('1')

    POLL_INTERVAL = const(20)  # ms; button self-poll period

    def __init__(self, pin, pull_up=True, name=''):
        if pull_up:  # most buttons
            self._hw_in = Signal(
                pin, Pin.IN, Pin.PULL_UP, invert=True)
        else:  # e.g. Pimoroni Plasma 2350 User button
            self._hw_in = Signal(
                pin, Pin.IN, invert=True)
        if name:
            self.name = name
        else:
            self.name = str(pin)        
        self.states = {'wait': self.name + self.WAIT,
                       'click': self.name + self.CLICK
                       }
        self.press_ev = asyncio.Event()  # starts cleared
        self.state = self.states['wait']

    async def poll_state(self):
        """ poll self for click event
            - event is set on button release
            - event handler must call clear_state
        """
        prev_pin_state = self._hw_in.value()
        while True:
            pin_state = self._hw_in.value()
            if pin_state != prev_pin_state:
                if not pin_state:
                    self.state = self.states['click']
                    self.press_ev.set()
                prev_pin_state = pin_state
            await asyncio.sleep_ms(self.POLL_INTERVAL)

    def clear_state(self):
        """ set state to 0 """
        self.state = self.states['wait']
        self.press_ev.clear()


class HoldButton(Button):
    """
        add button 'hold' state
        - T_HOLD sets hold time in ms
    """
    # additional button state
    HOLD = const('2')
    T_HOLD = const(750)  # ms - adjust as required

    def __init__(self, pin, pull_up=True, name=''):
        super().__init__(pin, pull_up, name)
        self.states['hold'] = self.name + self.HOLD

    async def poll_state(self):
        """
            poll self for click or hold events
            - ! button state must be cleared by event handler
            - elapsed time measured in ms
        """
        on_time = ticks_ms()
        prev_pin_state = self._hw_in.value()
        while True:
            pin_state = self._hw_in.value()
            if pin_state != prev_pin_state:
                time_stamp = ticks_ms()
                if pin_state:
                    on_time = time_stamp
                else:
                    if ticks_diff(time_stamp, on_time) < self.T_HOLD:
                        self.state = self.states['click']
                    else:
                        self.state = self.states['hold']
                    self.press_ev.set()
                prev_pin_state = pin_state
            await asyncio.sleep_ms(self.POLL_INTERVAL)


async def main():
    """ coro: test Button and HoldButton classes """

    # Plasma 2350 buttons
    buttons = {
        'A': HoldButton(12, pull_up=True, name='A'),
        'U': HoldButton(23, pull_up=False, name='U')
    }

    async def keep_alive():
        """ coro: to be awaited """
        t = 0
        while t < 60:
            await asyncio.sleep(1)
            t += 1

    async def process_event(btn):
        """ coro: responds to button events """
        while True:
            # wait until press_ev is set
            await btn.press_ev.wait()
            print(btn.name, btn.state)
            btn.clear_state()

    # create tasks to test each button
    for b in buttons:
        asyncio.create_task(buttons[b].poll_state())  # self-poll
        asyncio.create_task(process_event(buttons[b]))  # respond to event
    print('System initialised')

    await keep_alive()  # run scheduler until keep_alive() times out


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()  # clear retained state
        print('execution complete')
