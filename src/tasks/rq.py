import ujson

from pydantic import BaseModel, Field
from typing import (
    Any,
    Awaitable,
    Callable,
    Never,
    Protocol,
    TypeVar,
    Generic,
    Mapping,
)
from uuid import UUID, uuid4

from redis import asyncio as aioredis
from tasks.exceptions import (
    RetriesExceededException,
    StreamTimeout,
    TaskCallableNotRegistered,
)

AnyAsyncFunc = Callable[..., Awaitable[Any]]


A = TypeVar("A", contravariant=True)
K = TypeVar("K", contravariant=True)


class TaskCallable(Protocol[A, K]):
    async def __call__(self, *args: A, **kwargs: K) -> bytes:
        ...


class RedisTaskSettings(BaseModel):

    retries: int = 3
    retry_count: int = 0


class TaskBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    meta: RedisTaskSettings = Field(default_factory=RedisTaskSettings)


class RedisTask(TaskBase, BaseModel):

    callback_key: str
    args: tuple[Any, ...]
    kwargs: Mapping[str, Any]

    def encode(self) -> str:
        return self.json()

    @classmethod
    def decode(cls, obj: bytes) -> "RedisTask":
        return cls(**ujson.loads(obj))


class ParsedTask(Generic[A, K], RedisTask, BaseModel):

    fn: AnyAsyncFunc
    args: tuple[A, ...]
    kwargs: Mapping[str, K]

    redis_id: str

    def get_future(self) -> Awaitable[Any]:
        return self.fn(*self.args, **self.kwargs)

    class Config:
        arbitrary_types_allowed = True
        json_dumps = ujson.dumps


class AsyncTaskWrapper:
    def __init__(
        self, callback: AnyAsyncFunc, queue: "RedisStreamQueue", **kwargs: Any
    ) -> None:
        self.callback = callback
        self.queue = queue
        self.meta = RedisTaskSettings(**kwargs)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return await self.callback(*args, **kwargs)

    async def submit(self, *args: Any, **kwargs: Any) -> None:
        await self.queue.enqueue(self.callback, self.meta, *args, **kwargs)


class RedisStreamQueue:

    handlers: dict[str, AnyAsyncFunc] = {}

    def __init__(
        self,
        redis_client: "aioredis.Redis[bytes]",
        stream: str = "queue:pending",
    ) -> None:
        self.client = redis_client
        self.stream = stream

    def task(self, retries: int = 3, timeout: int = 60) -> Callable[..., Any]:
        def decorator(callback: AnyAsyncFunc) -> AsyncTaskWrapper:
            callback_key = callback.__name__
            self.handlers[callback_key] = callback
            return AsyncTaskWrapper(callback, self, retries=retries)

        return decorator

    async def _enqueue_task_object(self, task: RedisTask) -> RedisTask:
        await self.client.xadd(self.stream, {"payload": task.encode()})
        return task

    async def enqueue(
        self,
        callback: AnyAsyncFunc,
        meta: RedisTaskSettings | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> RedisTask:
        callback_key = callback.__name__
        task = RedisTask(
            callback_key=callback_key,
            meta=meta or RedisTaskSettings(),
            args=args,
            kwargs=kwargs,
        )
        return await self._enqueue_task_object(task)

    async def requeue(self, task: RedisTask) -> RedisTask | Never:
        retry_count = task.meta.retry_count
        if retry_count > task.meta.retries:
            raise RetriesExceededException(
                f"Максимальное число попыток: {task.meta.retries}"
            )
        task.meta.retry_count += 1
        return await self._enqueue_task_object(task)

    async def register_group(self, groupname: str) -> None:
        try:
            await self.client.xgroup_create(self.stream, groupname, mkstream=True)
        except Exception:
            pass

    def parse_task(
        self, raw_task: tuple[bytes, dict[bytes, bytes]]
    ) -> ParsedTask[Any, Any]:
        task_id, task_body = raw_task
        task_obj = RedisTask.decode(task_body[b"payload"])
        callback = self.handlers.get(task_obj.callback_key)
        if not callback:
            raise TaskCallableNotRegistered
        return ParsedTask(
            redis_id=task_id.decode("utf-8"), fn=callback, **task_obj.dict()
        )

    async def dequeue(
        self, groupname: str, consumername: str, block_timeout: int = 5000
    ) -> ParsedTask[Any, Any] | Never:

        raw_task = await self.client.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams={self.stream: ">"},
            block=block_timeout,
            count=1,
        )
        if not raw_task:
            raise StreamTimeout

        return self.parse_task(raw_task[0][1][0])

    async def reanimate(self, group: str, consumer: str) -> list[ParsedTask[Any, Any]]:

        _, pending, _ = await self.client.xautoclaim(
            self.stream, group, consumer, min_idle_time=1500
        )
        return [self.parse_task(pending_task) for pending_task in pending]

    async def delete(self, groupname: str, *ids: str | UUID) -> None:

        async with self.client.pipeline() as pipe:
            pipe.multi()  # type: ignore
            pipe.xack(self.stream, groupname, *ids)  # type: ignore
            pipe.xdel(self.stream, *ids)  # type: ignore
            await pipe.execute()  # type: ignore
