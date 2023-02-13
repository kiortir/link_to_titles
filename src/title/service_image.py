import base64
import mimetypes
import re
from typing import Any, AsyncGenerator, cast

import aiohttp
import yarl
from pydantic import AnyHttpUrl

from title.service_aiohttp import fetch


def extract_img_sources(img_tag: Any) -> list[str]:
    source = img_tag.get("src")
    if not source:
        sourceset = img_tag.get("srcset") or ""
        if not sourceset:
            return []
        return [s.split()[0] for s in sourceset.split(", ")]
    return [
        source,
    ]


async def aiterify(b: bytes) -> AsyncGenerator[bytes, None]:
    yield b


async def extraсt_data_from_base64(
    source: str, *_: Any
) -> tuple[str, AsyncGenerator[bytes, None]]:
    match = re.match("^data:image/(.+);base64,(.*)", source)
    if not match:
        raise ValueError

    ext, c = match.groups()
    r = base64.b64decode(c)
    return "." + ext, aiterify(r)


async def guess_ext(url: AnyHttpUrl, content_type: str | None) -> str:
    if content_type and (ext := mimetypes.guess_extension(content_type)):
        return ext

    return "." + yarl.URL(url).suffix


async def extraсt_data_from_url(
    source: AnyHttpUrl | str, session: aiohttp.ClientSession
) -> tuple[str, aiohttp.streams.AsyncStreamIterator[bytes]]:

    source = cast(AnyHttpUrl, source)
    response = await fetch(source, session)

    if not response:
        raise ValueError

    content_type = response.headers.get("content-type")
    ext = await guess_ext(source, content_type)

    return ext, response.content.iter_any()
