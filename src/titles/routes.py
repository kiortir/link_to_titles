from fastapi import APIRouter

from src.titles.entities import LinksPayload, LinksWithTitles
from src.titles.handlers import extract_titles

router = APIRouter()


@router.post("/titles", response_model=LinksWithTitles)
async def get_titles(payload: LinksPayload) -> LinksWithTitles:

    titled_links = await extract_titles(payload.links)
    return LinksWithTitles(links=titled_links)
