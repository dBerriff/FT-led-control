# queue.py

import asyncio

class Buffer:
    """
        Single item buffer
        - put_lock & het_lock support multiple data producers and consumers
        - Event.set() "must be called from within a task" - hence coros.
    """

    def __init__(self):
        self._item = None
        self.is_data = asyncio.Event()
        self.is_space = asyncio.Event()
        self.put_lock = asyncio.Lock()
        self.get_lock = asyncio.Lock()
        self.is_space.set()

    async def put(self, item):
        """ coro: add item to buffer
            - put_lock supports multiple producers
        """
        async with self.put_lock:
            await self.is_space.wait()
            self._item = item
            self.is_data.set()
            self.is_space.clear()

    async def get(self):
        """ coro: remove item from buffer
            - get_lock supports multiple consumers
        """
        async with self.get_lock:
            await self.is_data.wait()
            self.is_data.clear()
            self.is_space.set()
            return self._item


class Queue:
    """ FIFO queue
        - using array rather than list gave no measurable advantages
    """

    def __init__(self, length):
        super().__init__()
        self.length = length
        self.is_data = asyncio.Event()
        self.is_space = asyncio.Event()
        self.put_lock = asyncio.Lock()
        self.get_lock = asyncio.Lock()
        self.is_space.set()
        self.queue = [None] * length
        self.head = 0
        self.next = 0

    async def put(self, item):
        """ coro: add item to the queue """
        async with self.put_lock:
            await self.is_space.wait()
            self.queue[self.next] = item
            self.next = (self.next + 1) % self.length
            if self.next == self.head:
                self.is_space.clear()
            self.is_data.set()

    async def get(self):
        """ coro: remove item from the queue """
        async with self.get_lock:
            await self.is_data.wait()
            item = self.queue[self.head]
            self.head = (self.head + 1) % self.length
            if self.head == self.next:
                self.is_data.clear()
            self.is_space.set()
            return item

    @property
    def q_len(self):
        """ number of items in the queue """
        if self.head == self.next:
            n = self.length if self.is_data.is_set() else 0
        else:
            n = (self.next - self.head) % self.length
        return n
