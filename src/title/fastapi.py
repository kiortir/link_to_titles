from fastapi import APIRouter

from title import entity
from title import service

router = APIRouter()


@router.post("/titles", response_model=entity.LinksWithTitles)
async def get_titles(payload: entity.LinksPayload) -> entity.LinksWithTitles:

    titled_links = await service.extract_titles(payload.links)
    return entity.LinksWithTitles(links=titled_links)
