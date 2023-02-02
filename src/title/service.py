import asyncio
import re

import aiohttp

from title.entity import LinkWithTitle

_TITLE_REGEXP = re.compile(r"(?:<title(?:.*)>)(.*)(?:<\/title>)")


async def extract_titles(urls: list[str]) -> list[LinkWithTitle]:
    async with aiohttp.ClientSession() as session:
        futures = [map_title_to_link(url, session) for url in urls]
        titled_links: list[LinkWithTitle] = await asyncio.gather(*futures)
    return titled_links


async def map_title_to_link(link: str, session: aiohttp.ClientSession) -> LinkWithTitle:

    response = await session.get(link)  # проверять ли content-type?
    content = await response.text()

    title = get_title(content)
    return LinkWithTitle(url=link, title=title)


def get_title(content: str) -> str | None:
    title_content_match: re.Match[str] | None = _TITLE_REGEXP.search(content)
    return title_content_match.group(1) if title_content_match else None
