"""Leitura do Supabase (Postgres do app Gana).

Mapeamento (ver `supabase/migrations/`):

  users      -> User (só id, birth_date, consentimentos e favorite_genres)
  book_cache -> Book (o id de junção é o google_books_id)
  user_book  -> Interaction (status; o rating vem de STATUS_RATING)

Pontos do banco real, herdados da POC:
  - `user_book` guarda o `google_books_id`, não o id do `book_cache`;
  - UUIDs vêm em minúsculas e o app envia em maiúsculas: normalizamos;
  - as reviews com nota ficam fora do Postgres (no DynamoDB), então aqui o
    sinal é só o implícito do status.

A chave usada é a service_role: o serviço lê tabelas protegidas por RLS do lado
do servidor. Ela nunca vai para o app nem para o repositório.
"""

from __future__ import annotations

from datetime import date

from gana.domain import STATUS_RATING, Book, Interaction, User, normalize_user_id

_PAGE_SIZE = 1000  # o supabase-py limita o select em 1000 linhas por padrão
_USER_COLUMNS = "id, birth_date, personalization_consent, parental_consent, favorite_genres"


class SupabaseSource:
    def __init__(self, client):
        self._client = client

    def validate(self) -> None:
        for table in ("users", "book_cache", "user_book"):
            self._client.table(table).select("*").limit(1).execute()

    def get_users(self) -> list[User]:
        users = []
        for row in self._fetch_all("users", _USER_COLUMNS):
            if row.get("id") is None:
                continue
            birth = row.get("birth_date")
            users.append(
                User(
                    user_id=normalize_user_id(str(row["id"])),
                    birth_date=date.fromisoformat(birth) if birth else None,
                    personalization_consent=bool(row.get("personalization_consent")),
                    parental_consent=bool(row.get("parental_consent")),
                    favorite_genres=list(row.get("favorite_genres") or []),
                )
            )
        return users

    def get_books(self) -> list[Book]:
        books = []
        for row in self._fetch_all("book_cache"):
            gid = row.get("google_books_id")
            if not gid:
                continue
            books.append(
                Book(
                    google_books_id=gid,
                    title=row.get("title") or "",
                    author=list(row.get("author") or []),
                    main_category=row.get("main_category") or "",
                    categories=list(row.get("categories") or []),
                    pages=row.get("pages") or 0,
                    year_published=row.get("year_published") or 0,
                    url_image=row.get("url_image"),
                    language=row.get("language") or "pt",
                    maturity_rating=row.get("maturity_rating") or "NOT_MATURE",
                    isbn=row.get("isbn"),
                    publisher=row.get("publisher"),
                )
            )
        return books

    def get_interactions(self) -> list[Interaction]:
        interactions = []
        for row in self._fetch_all("user_book", "id_user, google_books_id, status"):
            uid, gid, status = row.get("id_user"), row.get("google_books_id"), row.get("status")
            if uid is None or not gid:
                continue
            status = status if status in STATUS_RATING else "Quero ler"
            interactions.append(Interaction(normalize_user_id(str(uid)), gid, status))
        return interactions

    def upsert_books(self, books: list[Book], descriptions: dict[str, str] | None = None) -> None:
        rows = []
        for book in books:
            row = book.to_api()
            row.pop("book_id")
            row |= {
                "isbn": book.isbn,
                "publisher": book.publisher,
                "language": book.language,
                "maturity_rating": book.maturity_rating,
                "description": (descriptions or {}).get(book.google_books_id),
            }
            rows.append(row)
        self._client.table("book_cache").upsert(rows, on_conflict="google_books_id").execute()

    def _fetch_all(self, table: str, columns: str = "*") -> list[dict]:
        rows: list[dict] = []
        start = 0
        while True:
            response = self._client.table(table).select(columns).range(start, start + _PAGE_SIZE - 1).execute()
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < _PAGE_SIZE:
                return rows
            start += _PAGE_SIZE
