from title.service import get_title

def test_title_extractor() -> None:

    titles = [
        '<title>MyTitle</title>',
        '<title randomattr="true">MyTitle</title>',
    ]
    assert all([get_title(title) == 'MyTitle' for title in titles])