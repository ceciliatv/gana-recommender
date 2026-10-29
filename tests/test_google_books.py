import json
from pathlib import Path

import httpx
import pytest

from gana.google_books import BASE_URL, GoogleBooksClient, GoogleBooksError, normalize

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "google_books_search.json").read_text())


def _client(responses: list[httpx.Response], calls: list) -> GoogleBooksClient:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return responses[min(len(calls), len(responses)) - 1]

    http = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    return GoogleBooksClient(api_key="chave-teste", client=http, backoff=0)


def test_normalize_full_volume():
    volume = normalize(FIXTURE["items"][0])
    book = volume.book
    assert book.google_books_id == "lL2GDwAAQBAJ"
    assert book.isbn == "9789896605858"  # ISBN-13 tem preferência
    assert book.main_category == "Fiction" and book.categories == ["Fiction", "Literary"]
    assert book.year_published == 2019 and book.pages == 237
    assert book.url_image.startswith("https://")
    assert book.maturity_rating == "NOT_MATURE"
    assert volume.description is None


def test_normalize_mature_isbn10_and_dates():
    book = normalize(FIXTURE["items"][1]).book
    assert book.maturity_rating == "MATURE"
    assert book.isbn == "0000000000"
    assert book.year_published == 2011
    assert book.categories == ["Fiction", "Romance", "Erotica"]
    assert book.url_image is None


def test_normalize_minimal_volume():
    book = normalize(FIXTURE["items"][2]).book
    assert book.title == "Livro Sem Categoria"
    assert book.main_category == "" and book.categories == [] and book.year_published == 0


def test_search_sends_key_and_normalizes():
    calls: list = []
    client = _client([httpx.Response(200, json=FIXTURE)], calls)
    volumes = client.search("torto arado", lang="pt", max_results=3)
    assert [v.book.google_books_id for v in volumes] == ["lL2GDwAAQBAJ", "exemplo-mature", "exemplo-sem-categoria"]
    params = calls[0].url.params
    assert params["key"] == "chave-teste" and params["langRestrict"] == "pt" and params["q"] == "torto arado"


def test_retry_after_429_then_success():
    calls: list = []
    client = _client([httpx.Response(429), httpx.Response(200, json=FIXTURE)], calls)
    assert len(client.search("x")) == 3
    assert len(calls) == 2


def test_gives_up_after_three_429():
    calls: list = []
    client = _client([httpx.Response(429)] * 5, calls)
    with pytest.raises(GoogleBooksError, match="GOOGLE_BOOKS_API_KEY"):
        client.search("x")
    assert len(calls) == 3


def test_does_not_retry_404():
    calls: list = []
    client = _client([httpx.Response(404)], calls)
    with pytest.raises(GoogleBooksError):
        client.get("nao-existe")
    assert len(calls) == 1


def test_same_query_is_cached():
    calls: list = []
    client = _client([httpx.Response(200, json=FIXTURE)], calls)
    client.search("cache")
    client.search("cache")
    assert len(calls) == 1
