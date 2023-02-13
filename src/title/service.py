import asyncio
import logging
from pathlib import Path
from typing import Any, AsyncIterator, cast
from uuid import UUID

import aiofiles
import aiohttp
import yarl
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

from settings import settings
from title import entity, postgres, service_image
from title.service_aiohttp import fetch

logger = logging.getLogger("title")


async def save_file(fp: str | Path, obj_stream: AsyncIterator[bytes]) -> None:
    async with aiofiles.open(fp, mode="wb") as f:
        async for chunk in obj_stream:
            await f.write(chunk)


def normalize_url(url: str, origin_url: AnyHttpUrl) -> AnyHttpUrl | str:
    if url.startswith("data"):
        return url

    url_obj = yarl.URL(url)

    if not url_obj.is_absolute():
        origin = yarl.URL(origin_url)
        origin_host = origin.host
        if origin.host:
            url_obj = origin.join(url_obj)

    return cast(AnyHttpUrl, str(url_obj.with_scheme(scheme="https")))


def parse_page(page: str, page_url: AnyHttpUrl) -> entity.PageContent:

    soup = BeautifulSoup(page, "lxml")

    title = t.text if (t := soup.find("title")) else None

    sources: list[str] = []
    for img in soup.find_all("img"):
        sources.extend(service_image.extract_img_sources(img))
    sources = [normalize_url(src, page_url) for src in sources]

    return entity.PageContent(title=title, image_sources=sources)


async def process_image(
    image_source: AnyHttpUrl | str,
    session: aiohttp.ClientSession,
    processed_link_id: int,
) -> None:

    image = await postgres.create_image(image_source, processed_link_id)
    if image_source.startswith("data"):
        f = service_image.extraсt_data_from_base64
    else:
        f = service_image.extraсt_data_from_url

    try:
        ext, raw_image = await f(image_source, session)
    except ValueError:
        await postgres.update_image_status(image.id, entity.LinkStatus.ERROR)
        logger.info(f"image {image_source} could not be fetched")
        return

    await postgres.update_image_ext(image.id, ext)
    image.ext = ext
    await save_file(image.get_path(), raw_image)
    await postgres.update_image_status(image.id, entity.LinkStatus.DONE)
    logger.info(f"image {image_source} saved")


async def process_link(
    link: AnyHttpUrl, session: aiohttp.ClientSession, request_session_id: UUID
) -> None:

    response = await fetch(link, session, retries=3)

    if not response:
        return

    if response.headers.get("content-type") != "text/html":
        logger.warning(f"{link} response is probably not an html")

    processed_link_id = await postgres.create_processed_link(link)
    await postgres.create_session_link_relation(request_session_id, processed_link_id)

    response_content = await response.text()

    page_content = parse_page(response_content, link)

    if page_content.title is not None:
        await postgres.set_link_title(processed_link_id, page_content.title)

    await postgres.unbind_images(processed_link_id)

    async with asyncio.TaskGroup() as tg:
        for image_source in page_content.image_sources:
            tg.create_task(process_image(image_source, session, processed_link_id))

    await postgres.update_link_status(processed_link_id, entity.LinkStatus.DONE)


async def process_links(links: list[AnyHttpUrl], request_session_id: UUID) -> None:
    async with aiohttp.ClientSession() as session:
        async with asyncio.TaskGroup() as tg:
            for link in links:
                tg.create_task(process_link(link, session, request_session_id))
    logger.info(f"Session {request_session_id} done")
