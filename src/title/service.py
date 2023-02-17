import asyncio
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterator, cast, Callable, TypeVar
from uuid import UUID

import aiofiles
import aiohttp
import yarl
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

from settings import settings
from src.title import repository
from title import entity, service_image
from title.service_aiohttp import fetch

import re
import base64
import mimetypes

logger = logging.getLogger("title")


def get_title(
    soup: BeautifulSoup, unit: entity.PageContent
) -> tuple[BeautifulSoup, entity.PageContent]:

    title = soup.find("title")
    if title:
        unit.title = title.text

    return soup, unit


def get_imgs(
    soup: BeautifulSoup, unit: entity.PageContent
) -> tuple[BeautifulSoup, entity.PageContent]:
    ...

    return soup, unit


def get_extractor(
    *functions: Callable[
        [BeautifulSoup, entity.PageContent], tuple[BeautifulSoup, entity.PageContent]
    ]
) -> Callable[[BeautifulSoup, entity.PageContent], entity.PageContent]:
    def wrapper(soup: BeautifulSoup, unit: entity.PageContent) -> entity.PageContent:
        for f in functions:
            soup, unit = f(soup, unit)

        return unit

    return wrapper


def parse_page(page: str) -> entity.PageContent:

    soup = BeautifulSoup(page, "lxml")
    parsed_page = entity.PageContent(title=None, image_sources=[])

    extractor = get_extractor(get_title, get_imgs)

    return extractor(soup, parsed_page)


async def fetch(url: str | yarl.URL) -> aiohttp.ClientResponse:
    url = str(url)
    ...


async def process_url(url: yarl.URL) -> None:

    url_response = await fetch(str(url))
    url_content = await url_response.text()
    parsed_content = parse_page(url_content)

    id = await repository.create_processed_link(str(url))

    for image in parsed_content.image_sources:
        ...


def normalize_url(url: str | yarl.URL) -> yarl.URL:

    return yarl.URL()


async def aiterify(b: bytes) -> AsyncGenerator[bytes, None]:
    yield b


async def extraсt_data_from_base64(source: str) -> tuple[str, AsyncIterator[bytes]]:
    match = re.match("^data:image/(.+);base64,(.*)", source)
    if not match:
        raise ValueError

    ext, c = match.groups()
    r = base64.b64decode(c)
    return "." + ext, aiterify(r)


async def guess_ext(url: yarl.URL, content_type: str | None) -> str:
    if content_type and (ext := mimetypes.guess_extension(content_type)):
        return ext

    return "." + url.suffix


async def extraсt_data_from_url(
    source: yarl.URL,
) -> tuple[str, AsyncIterator[bytes]]:

    response = await fetch(source)

    if not response:
        raise ValueError

    content_type = response.headers.get("content-type")
    ext = await guess_ext(source, content_type)

    return ext, response.content.iter_any()


async def process_image_source(
    source: str, origin: yarl.URL, related_link_id: int
) -> None:

    if source.startswith("data"):
        ext, img_obj = await extraсt_data_from_base64(source)
    else:
        normalized_source = normalize_url(source)
        ext, img_obj = await extraсt_data_from_url(normalized_source)

    await repository.create_image(str(origin), related_link_id)
