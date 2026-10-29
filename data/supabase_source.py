"""
Fonte de dados que le usuarios, livros e interacoes direto do Supabase
(Postgres do app Gana). Expoe o MESMO contrato do mock_data:
get_users() / get_books() / get_interactions().

Mapeamento de schema (tabelas reais do app Gana):

  users      -> {user_id, username, name, is_private}
  book_cache -> {book_id (= google_books_id), google_books_id, title, author[],
                 main_category, categories[], pages, year_published, url_image, ...}
  user_book  -> interacao (id_user, google_books_id, status) -> rating implicito

Pontos importantes do banco real:
  - A juncao livro<->interacao e por `google_books_id` (a tabela `user_book`
    NAO guarda o id do book_cache, e sim o google_books_id). Por isso usamos
    `google_books_id` como identificador de livro em todo o algoritmo.
  - UUIDs sao normalizados para minusculas (o app iOS envia em maiusculas).
  - NAO existe tabela de reviews no Postgres (ficam no Dynamo), entao o sinal
    de rating aqui e SOMENTE implicito pelo status. Quando as reviews tiverem
    uma fonte, basta cruzar o `rate` aqui (ver _IMPLICIT_RATING).
"""
from __future__ import annotations
from typing import List, Tuple

# Rating implicito por status quando nao ha review explicita.
_IMPLICIT_RATING = {
    "Lido": 3.5,
    "Lendo": 3.0,
    "Quero ler": 2.0,
    "Abandonado": 1.0,
}

# Paginacao: o supabase-py limita o select em 1000 linhas por padrao.
_PAGE_SIZE = 1000


class SupabaseSource:
    """Le os dados do Supabase mantendo o contrato do mock_data."""

    def __init__(self, client):
        self._client = client

    def validate(self) -> None:
        """
        Confirma que as tabelas necessarias sao legiveis com a chave atual.
        Lanca excecao (capturada em build_source) se faltar permissao — o caso
        tipico de quem usou a chave anon/publishable em vez da service_role.
        """
        for table in ("users", "book_cache", "user_book"):
            self._client.table(table).select("*").limit(1).execute()

    # ── users ────────────────────────────────────────────────────────────────
    def get_users(self) -> List[dict]:
        users = []
        for row in self._fetch_all("users"):
            uid = row.get("id")
            if uid is None:
                continue
            users.append({
                "user_id": str(uid).lower(),
                "username": row.get("username") or "",
                "name": row.get("name") or row.get("username") or "",
                "is_private": bool(row.get("is_private", False)),
            })
        return users

    # ── book_cache ─────────────────────────────────────────────────────────────
    def get_books(self) -> List[dict]:
        books = []
        for row in self._fetch_all("book_cache"):
            gid = row.get("google_books_id")
            if not gid:
                continue
            books.append({
                "book_id": gid,                 # chave de juncao = google_books_id
                "google_books_id": gid,
                "isbn": row.get("isbn"),
                "title": row.get("title") or "",
                "author": row.get("author") or [],
                "pages": row.get("pages") or 0,
                "year_published": row.get("year_published") or 0,
                "publisher": row.get("publisher"),
                "main_category": row.get("main_category") or "",
                "categories": row.get("categories") or [],
                "language": row.get("language") or "pt",
                "url_image": row.get("url_image"),
            })
        return books

    # ── user_book -> interacoes ────────────────────────────────────────────────
    def get_interactions(self) -> List[Tuple[str, str, float]]:
        interactions = []
        for row in self._fetch_all("user_book"):
            uid = row.get("id_user")
            gid = row.get("google_books_id")
            status = row.get("status")
            if uid is None or not gid:
                continue
            rating = _IMPLICIT_RATING.get(status, _IMPLICIT_RATING["Quero ler"])
            interactions.append((str(uid).lower(), gid, rating))
        return interactions

    # ── util ───────────────────────────────────────────────────────────────────
    def _fetch_all(self, table: str) -> List[dict]:
        """Le todas as linhas da tabela, paginando para passar do limite default."""
        rows: List[dict] = []
        start = 0
        while True:
            response = (
                self._client.table(table)
                .select("*")
                .range(start, start + _PAGE_SIZE - 1)
                .execute()
            )
            batch = response.data or []
            rows.extend(batch)
            if len(batch) < _PAGE_SIZE:
                break
            start += _PAGE_SIZE
        return rows
