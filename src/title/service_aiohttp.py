import asyncio

import aiohttp
from pydantic import AnyHttpUrl


async def fetch(
    link: AnyHttpUrl, session: aiohttp.ClientSession, retries: int = 3, retry_timeout: int = 2
) -> aiohttp.ClientResponse | None:

    retry_counter = 0
    while retry_counter <= retries:
        try:
            r = await session.get(link, raise_for_status=True)
            break
        except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError):
            await asyncio.sleep(retry_timeout)
            retry_counter += 1
            continue
    else:
        return None

    return r
