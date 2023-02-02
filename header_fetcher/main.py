import re
import asyncio
from typing import TypedDict

import aiohttp
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LinksPayload(BaseModel):

    links: list[str]


class LinkWithTitle(TypedDict):

    url: str
    title: str | None


class LinksWithTitles(BaseModel):

    links: list[LinkWithTitle]


HEADER_REGEXP = re.compile(r"(?:<head(?:.*)>)((?:.|\n)*)(?:<\/head>)")
TITLE_REGEXP = re.compile(r"(?:<title(?:.*)>)((?:.|\n)*)(?:<\/title>)")


async def map_title_to_link(link: str, session: aiohttp.ClientSession) -> LinkWithTitle:

    response = await session.get(link) # проверять ли content-type?
    content = await response.text()
    
    title = get_title(content)
    return {"url": link, "title": title}


def get_title(content: str) -> str | None:
    head_content_match: re.Match[str] | None = HEADER_REGEXP.search(
        content
    )  # что делать, если title не в head? нужно ли на это вообще обращать внимание?
    if not head_content_match:
        return None
    title_content_match: re.Match[str] | None = TITLE_REGEXP.search(head_content_match.group(0))
    if not title_content_match:
        return None
    return title_content_match.group(1)


@app.post("/titles", response_model=LinksWithTitles)
async def get_titles(payload: LinksPayload):

    async with aiohttp.ClientSession() as session:
        futures = [map_title_to_link(url, session) for url in payload.links]
        titled_links = await asyncio.gather(*futures)

    return LinksWithTitles(links=titled_links)
