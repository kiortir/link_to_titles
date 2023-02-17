import asyncio
from typing import Awaitable, Any
from rq import Queue


class Worker:
    def __init__(self, queue: Queue, max_tasks: int = 5):
        if max_tasks < 1:
            raise AttributeError("max_tasks cannot be less then 1")
        self.queue = queue
        self.sem = asyncio.Semaphore(max_tasks)

    async def execute(self, fn: Awaitable[Any]) -> None:
        try:
            await fn
        finally:
            self.sem.release()

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        sem = self.sem
        while True:
            await sem.acquire()
            task = await self.queue.dequeue()
            if not task:
                sem.release()
                continue

            # https://github.com/microsoft/pylance-release/issues/184?ysclid=le8mw1b48w310681535
            loop.create_task(self.execute(task))  # type: ignore


async def worker(queue: Queue, count: int) -> None:
    loop = asyncio.get_event_loop()
    while True:
        task = queue.dequeue()
        loop.create_task(task)
