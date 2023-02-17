from typing import cast

import aiohttp
import pytest
from pydantic import AnyHttpUrl

from title.service_aiohttp import fetch


@pytest.mark.asyncio
async def test_basic_fetch() -> None:
    async with aiohttp.ClientSession() as session:
        r = await fetch(cast(AnyHttpUrl, "https://httpbin.org/get"), session)
        assert r
        assert r.status == 200


@pytest.mark.asyncio
async def test_retries() -> None:
    async with aiohttp.ClientSession() as session:
        r = await fetch(cast(AnyHttpUrl, "https://httpbin.org/status/400"), session)
        assert r is None