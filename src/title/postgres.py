from dataclasses import asdict
from typing import Any, cast
from uuid import UUID

from pydantic import AnyHttpUrl

from db import pool
from settings import settings
from title import entity


async def create_session() -> UUID:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute("INSERT INTO session DEFAULT VALUES RETURNING id")
            excution_response: tuple[UUID] | None = await cur.fetchone()
            if not excution_response:
                raise Exception
            (session_id,) = excution_response
            return session_id


async def get_session_by_id(id: UUID) -> entity.SessionOut:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                """
                SELECT 
                    pl.url,
                    pl.title,
                    (SELECT array(SELECT (origin, %s || id || ext, status) FROM image WHERE image.link_id=pl.id)),
                    pl.status
                FROM 
                    session s
                    LEFT JOIN session_link sl ON sl.session_id=s.id
                    LEFT JOIN processed_link pl ON pl.id=sl.processed_link_id
                WHERE s.id=%s
                GROUP BY 
                    pl.id,
                    pl.url, 
                    pl.title,
                    pl.status
            """,
                (settings.media_root, id),
            )
            r: list[
                tuple[str, str, list[tuple[str, str, entity.LinkStatus]], str]
            ] | None = await cur.fetchall()

            if not r:
                raise ValueError
            links = [
                entity.LinkOut(
                    url=cast(AnyHttpUrl, url),
                    title=title,
                    images=[
                        entity.ImageOut(
                            origin=origin,
                            url=url,
                            status=status,
                        )
                        for origin, url, status in images
                    ],
                    status=entity.LinkStatus(status),
                )
                for url, title, images, status in r
            ]

            session = entity.SessionOut(
                links=links,
            )
            return session


async def create_processed_link(url: str) -> int:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            # TODO: написать нормально
            await cur.execute(
                """
                INSERT INTO processed_link(url) VALUES(%s)
                ON CONFLICT (url) 
                    DO UPDATE SET
                        url=EXCLUDED.url
                RETURNING id
                """,
                (url,),
            )
            r: tuple[int, Any] | None = await cur.fetchone()
            if not r:
                raise Exception
            link_id, *_ = r
            return link_id


async def get_processed_link(url: str) -> int | None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute("SELECT * FROM processed_link WHERE url=%s", (url,))
            r: tuple[int, Any] | None = await cur.fetchone()
            if not r:
                return None
            link_id, *_ = r
            return link_id


async def set_link_title(link_id: int, title: str) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "UPDATE processed_link SET title=%s WHERE id=%s", (title, link_id)
            )


async def update_link_status(link_id: int, status: entity.LinkStatus) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "UPDATE processed_link SET status=%s WHERE id=%s", (status, link_id)
            )


async def create_session_link_relation(
    session_id: UUID, processed_link_id: int
) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "INSERT INTO session_link(session_id, processed_link_id) VALUES(%s, %s)",
                (session_id, processed_link_id),
            )


async def unbind_images(link_id: int) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                """
                    UPDATE image 
                    SET link_id=NULL
                    WHERE link_id=%s 
                    RETURNING id
                    """,
                (link_id,),
            )
            ids = await cur.fetchall()


async def create_image(origin: str | AnyHttpUrl, link_id: int) -> entity.ImageDB:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            # TODO: написать нормально
            await cur.execute(
                """
                INSERT INTO image (origin, link_id) VALUES(%s, %s)
                ON CONFLICT (origin) 
                    DO UPDATE SET
                        link_id=%s
                RETURNING id
                """,
                (origin, link_id, link_id),
            )
            r: tuple[UUID, Any] | None = await cur.fetchone()
            if not r:
                raise Exception
            image_id, *_ = r
            return entity.ImageDB(link_id=link_id, id=image_id, origin=origin)


async def update_image_status(image_id: UUID, status: entity.LinkStatus) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "UPDATE image SET status=%s WHERE id=%s", (status, image_id)
            )


async def update_image_ext(image_id: UUID, ext: str) -> None:
    async with pool.connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute("UPDATE image SET ext=%s WHERE id=%s", (ext, image_id))
