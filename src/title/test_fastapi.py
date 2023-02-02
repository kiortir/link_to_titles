from asgi import app
from fastapi.testclient import TestClient

client = TestClient(app)

tested_links = {
        "links": [
            {"url": "https://google.com", "title": "Google"},
            {
                "url": "https://unirock.ru",
                "title": "Изделия из искусственного и натурального камня — Unirock",
            },
            {"url": "https://habr.ru", "title": "All posts in a row / Habr"},
        ]
    }


def test_title_fetcher() -> None:
    response = client.post("/titles", json={"links": [link["url"] for link in tested_links["links"]]})
    assert response.json() == tested_links