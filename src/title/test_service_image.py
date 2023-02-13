from typing import cast

from bs4 import BeautifulSoup

from title import service_image


def test_source_extraction() -> None:

    image_tags = map(
        lambda x: BeautifulSoup(x, "lxml").find("img"),  # type: ignore
        [
            '<img src="test_source">',
            '<img srcset="test_source 2x, test_source 100px">',
            '<img>',
        ],
    )
    for tag in image_tags:
        print(tag)
        sources = service_image.extract_img_sources(tag)
        assert all(src == "test_source" for src in sources)
