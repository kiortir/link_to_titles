import asyncio
import logging
import multiprocessing
import os
from typing import Any

from tasks.rq import ParsedTask, RedisStreamQueue

from redis_client import queue
from tasks.exceptions import StreamTimeout
from title.service import *

FORMAT = "%(asctime)s - [%(levelname)s] - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("worker")
logger.setLevel(logging.DEBUG)


class WorkerManager:
    def __init__(self, max_workers: int = 4, groupname: str = "main-worker-group"):
        self.max_workers = min(multiprocessing.cpu_count(), max_workers)
        self.processes = []  # type: ignore
        self.groupname = groupname

    def __enter__(self) -> 'WorkerManager':
        for i in range(self.max_workers):
            shutdown_event = multiprocessing.Event()
            process = multiprocessing.Process(
                target=start_worker,
                kwargs={
                    "queue": queue,
                    "shutdown_event": shutdown_event,
                    "group": self.groupname,
                    "consumer": f"worker_{i}",
                },
            )
            self.processes.append((process, shutdown_event))
        return self
    
    def run(self) -> None:
        asyncio.run(queue.register_group(self.groupname))


        for process, _ in self.processes:
            process.start()
        for process, _ in self.processes:
            process.join()

    def __exit__(self, *_: Any) -> None:
        for _, event in self.processes:
            event.set()
        for process, _ in self.processes:
            process.join()
            process.close()


class Worker:
    def __init__(self, queue: RedisStreamQueue, groupname: str, consumername: str):
        self.queue = queue
        self.groupname = groupname
        self.consumername = consumername

    async def apply(self, task: ParsedTask) -> None:
        async def execute_and_ack() -> None:
            try:
                await task.get_future()
                await self.queue.delete(self.groupname, task.redis_id)
            except Exception:
                await self.queue.requeue(task)

        future = execute_and_ack()
        asyncio.ensure_future(future)

    async def start(
        self,
        shutdown_event: Any = None,
    ) -> None:

        while not shutdown_event.is_set():

            deserted = await self.queue.reanimate(self.groupname, self.consumername)
            for task in deserted:
                await self.apply(task)

            try:
                task = await self.queue.dequeue(self.groupname, self.consumername)
                await self.apply(task)

            except StreamTimeout:
                continue

    def run(self, shutdown_event: Any) -> None:
        asyncio.run(self.start(shutdown_event))


def start_worker(
    queue: RedisStreamQueue, 
    group: str,
    consumer: str,
    shutdown_event: Any = None
) -> None:
    logger.debug(f"Воркер запущен: {os.getpid()}")
    worker = Worker(queue, group, consumer)
    worker.run(shutdown_event)


def run(workers: int = 4) -> None:
    with WorkerManager(workers) as manager:
        manager.run()


if __name__ == "__main__":
    run()
