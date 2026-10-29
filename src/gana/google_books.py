"""Cliente da Google Books API (spec 004).

Busca e normaliza livros para o formato do `book_cache`. A chave é opcional,
mas a cota anônima é compartilhada e acaba rápido (durante o desenvolvimento ela
devolveu 429), então use `GOOGLE_BOOKS_API_KEY` em produção.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from gana.domain import Book

BASE_URL = "https://www.googleapis.com/books/v1"
RETRY_STATUS = {429, 500, 502, 503, 504}


class GoogleBooksError(RuntimeError):
    pass


@dataclass
class NormalizedVolume:
    book: Book
    description: str | None  # só em tempo de execução; nunca versionada


def _isbn(info: dict) -> str | None:
    ids = {i.get("type"): i.get("identifier") for i in info.get("industryIdentifiers") or []}
    return ids.get("ISBN_13") or ids.get("ISBN_10")


def _year(published: str | None) -> int:
    if published and published[:4].isdigit():
        return int(published[:4])
    return 0


def _categories(raw: list[str] | None) -> tuple[str, list[str]]:
    """ "Fiction / Fantasy / Epic" vira main_category "Fiction" e categorias [Fiction, Fantasy, Epic]."""
    flat: list[str] = []
    for entry in raw or []:
        for part in entry.split("/"):
            part = part.strip()
            if part and part not in flat:
                flat.append(part)
    return (flat[0] if flat else ""), flat


def normalize(volume: dict) -> NormalizedVolume:
    info = volume.get("volumeInfo") or {}
    main, categories = _categories(info.get("categories"))
    image = (info.get("imageLinks") or {}).get("thumbnail")
    if image and image.startswith("http://"):
        image = "https://" + image[len("http://") :]
    book = Book(
        google_books_id=volume["id"],
        title=info.get("title", "").strip(),
        author=list(info.get("authors") or []),
        main_category=main,
        categories=categories,
        pages=int(info.get("pageCount") or 0),
        year_published=_year(info.get("publishedDate")),
        url_image=image,
        language=info.get("language") or "pt",
        maturity_rating=info.get("maturityRating") or "NOT_MATURE",
        isbn=_isbn(info),
        publisher=info.get("publisher"),
    )
    return NormalizedVolume(book, info.get("description"))


class GoogleBooksClient:
    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        max_attempts: int = 3,
        backoff: float = 1.0,
        cache_ttl: float = 3600.0,
    ):
        self.api_key = api_key
        self.http = client or httpx.Client(base_url=BASE_URL, timeout=15)
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.cache_ttl = cache_ttl
        self._cache: dict[tuple, tuple[float, dict]] = {}

    def _get(self, path: str, params: dict) -> dict:
        if self.api_key:
            params = params | {"key": self.api_key}
        key = (path, tuple(sorted((k, str(v)) for k, v in params.items() if k != "key")))
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl:
            return cached[1]
        for attempt in range(1, self.max_attempts + 1):
            response = self.http.get(path, params=params)
            if response.status_code == 200:
                data = response.json()
                self._cache[key] = (time.monotonic(), data)
                return data
            if response.status_code not in RETRY_STATUS or attempt == self.max_attempts:
                break
            time.sleep(self.backoff * 2 ** (attempt - 1))
        hint = " (cota esgotada: configure GOOGLE_BOOKS_API_KEY)" if response.status_code == 429 else ""
        raise GoogleBooksError(f"Google Books respondeu {response.status_code} em {path}{hint}")

    def search(self, query: str, lang: str | None = None, max_results: int = 20) -> list[NormalizedVolume]:
        params: dict = {"q": query, "maxResults": max(1, min(max_results, 40)), "printType": "books"}
        if lang:
            params["langRestrict"] = lang
        data = self._get("/volumes", params)
        return [normalize(v) for v in data.get("items") or [] if v.get("id")]

    def get(self, volume_id: str) -> NormalizedVolume:
        return normalize(self._get(f"/volumes/{volume_id}", {}))
