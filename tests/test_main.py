from header_fetcher.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

test_links = {
    "links": [
        "https://google.com",
        "https://ya.ru",
        "https://unirock.ru",
        "https://habr.ru",
    ]
}

def test_title_fetcher():
    response = client.post("/titles", 
        json = test_links
    )
    print(response.text)