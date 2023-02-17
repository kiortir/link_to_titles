import json
from dataclasses import Field, asdict, dataclass
from functools import wraps
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid4

from redis import asyncio as aioredis

AnyAsyncFunc = Callable[..., Awaitable[Any]]


class AsyncTaskWrapper:
    def __init__(self, callback: AnyAsyncFunc, queue: "Queue") -> None:
        self.__call__ = callback
        self.queue = queue

    # async def __call__(self, *args: Any, **kwargs: Any) -> Any:
    #     return await self.callback(*args, **kwargs)

    async def submit(self, *args: Any, **kwargs: Any) -> None:
        await self.queue.enqueue(self.__call__, *args, **kwargs)


@dataclass
class RedisTask:
    callback_key: str
    encoded_args: str
    encoded_kwargs: str
    _id: UUID = Field(default_factory=uuid4)  # type: ignore

    def encode(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def decode(cls, obj: bytes) -> "RedisTask":
        return RedisTask(**json.loads(obj))


class Queue:
    handlers: dict[str, AnyAsyncFunc] = {}

    def __init__(
        self, redis_client: aioredis.Redis[Any], queue_name: str = "queue:tasks"
    ) -> None:
        self.client = redis_client
        self.queue_name = queue_name

    def task(self, retries: int = 3, timeout: int = 60) -> Callable[..., Any]:
        def decorator(callback: AnyAsyncFunc) -> AsyncTaskWrapper:
            callback_key = callback.__name__
            self.handlers[callback_key] = callback
            return AsyncTaskWrapper(callback, self)

        return decorator

    async def enqueue(self, callback: AnyAsyncFunc, *args: Any, **kwargs: Any) -> UUID:
        callback_key = ""
        encoded_args = "{%}".join(args)
        encoded_kwargs = json.dumps(kwargs)
        task = RedisTask(callback_key, encoded_args, encoded_kwargs)
        await self.client.rpush(self.queue_name, task.encode())
        return task._id

    async def dequeue(self) -> Awaitable[Any] | None:

        task_raw = (await self.client.blpop(self.queue_name))[0]
        task = RedisTask.decode(task_raw)
        args = task.encoded_args.split("{%}")
        kwargs = json.loads(task.encoded_kwargs)
        callback = self.handlers.get(task.callback_key)
        if not callback:
            return None
            
        return callback(*args, **kwargs)
