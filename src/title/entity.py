from enum import Enum
from pathlib import Path

from pydantic import UUID4, AnyHttpUrl, BaseModel

from settings import settings


class LinkStatus(Enum):
    PENDING = "PENDING"
    DONE = "DONE"
    ERROR = "ERROR"


class ImageBase(BaseModel):
    origin: str | None = None
    id: UUID4
    status: LinkStatus | None = None

    ext: str = ""

    def get_path(self) -> Path:
        return settings.media_path / (str(self.id) + self.ext)


class ImageDB(ImageBase):
    link_id: int


class ImageOut(BaseModel):
    origin: str
    url: str | AnyHttpUrl
    status: LinkStatus

    @classmethod
    def get_url(cls, id: UUID4, ext: str) -> str:
        return str(settings.media_root) + str(id) + str(ext)


class ProcessedLink(BaseModel):
    url: AnyHttpUrl
    title: str | None = None
    images: list[ImageBase]
    status: LinkStatus


class ProcessedLinkDB(ProcessedLink):
    id: int


class Session(BaseModel):
    links: list[ProcessedLink | ProcessedLinkDB]


class LinkOut(BaseModel):
    url: AnyHttpUrl
    title: str | None = None
    images: list[ImageOut]
    status: LinkStatus


class SessionOut(BaseModel):
    links: list[LinkOut]


class SessionDB(Session):
    id: UUID4


class LinksPayload(BaseModel):

    links: list[AnyHttpUrl]


class PageContent(BaseModel):
    title: str | None
    image_sources: list[str]
