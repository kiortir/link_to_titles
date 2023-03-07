from redis import asyncio as aioredis
from src.settings import settings
from typing import Any

from tasks.rq import RedisStreamQueue

client: "aioredis.Redis[bytes]" = aioredis.Redis(host=settings.redis_host, port=settings.redis_port)

queue = RedisStreamQueue(client, settings.redis_queue_name)