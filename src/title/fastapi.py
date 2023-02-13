from enum import Enum
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException

from title import entity, postgres, service

router = APIRouter()


class URLs(str, Enum):

    enqueue = "/enqueue"
    session = "/session/{session_id}"


@router.post(URLs.enqueue)
async def process_urls(
    payload: entity.LinksPayload, background_tasks: BackgroundTasks
) -> dict[str, str]:
    session_id = await postgres.create_session()
    background_tasks.add_task(service.process_links, payload.links, session_id)
    return {"url": URLs.session.format(session_id=session_id)}  # type: ignore


@router.get(URLs.session)
async def get_session(session_id: UUID) -> entity.SessionOut:
    try:
        session = await postgres.get_session_by_id(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} doesnt exist"
        )
    return session
