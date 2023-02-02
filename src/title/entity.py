from pydantic.dataclasses import dataclass


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
