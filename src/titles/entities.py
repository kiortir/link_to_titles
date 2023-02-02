from pydantic.dataclasses import dataclass


# Симпатичнее, конечно, но mypy захотел поругаться по-умолчанию)
@dataclass
class LinksPayload:

    links: list[str]


@dataclass
class LinkWithTitle:

    url: str
    title: str | None


@dataclass
class LinksWithTitles:

    links: list[LinkWithTitle]
