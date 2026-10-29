"""Fontes de dados e o estado em memória do serviço.

A fonte é o Supabase (Postgres do app) quando há credenciais; sem elas, ou se a
conexão falhar, o serviço sobe com os dados sintéticos de `mock.py`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import Protocol

from gana.config import Settings
from gana.data import mock
from gana.domain import Book, Interaction, User

log = logging.getLogger("gana")


class DataSource(Protocol):
    def get_users(self) -> list[User]: ...
    def get_books(self) -> list[Book]: ...
    def get_interactions(self) -> list[Interaction]: ...


class MockSource:
    def get_users(self) -> list[User]:
        return [replace(u, favorite_genres=list(u.favorite_genres)) for u in mock.USERS]

    def get_books(self) -> list[Book]:
        return list(mock.BOOKS)

    def get_interactions(self) -> list[Interaction]:
        return list(mock.INTERACTIONS)


def build_source(settings: Settings) -> tuple[DataSource, str]:
    if not settings.supabase_url or not settings.supabase_service_key:
        return MockSource(), "mock (defina SUPABASE_URL e SUPABASE_SERVICE_KEY para usar o banco)"
    try:
        from supabase import create_client

        from gana.data.supabase_source import SupabaseSource

        source = SupabaseSource(create_client(settings.supabase_url, settings.supabase_service_key))
        source.validate()
        return source, "supabase"
    except Exception as exc:  # pacote ausente, rede, credencial ou permissão
        log.warning("Supabase indisponível (%s); usando dados sintéticos.", type(exc).__name__)
        return MockSource(), "mock (fallback após erro no Supabase)"


@dataclass
class DataState:
    """Usuários, livros e interações carregados em memória."""

    users: dict[str, User] = field(default_factory=dict)
    books: dict[str, Book] = field(default_factory=dict)
    interactions: list[Interaction] = field(default_factory=list)

    @classmethod
    def load(cls, source: DataSource) -> DataState:
        books = {b.book_id: b for b in source.get_books()}
        interactions = [i for i in source.get_interactions() if i.book_id in books]
        return cls({u.user_id: u for u in source.get_users()}, books, interactions)

    def interactions_of(self, user_id: str) -> list[Interaction]:
        return [i for i in self.interactions if i.user_id == user_id]

    def upsert_interaction(self, interaction: Interaction) -> None:
        self.interactions = [
            i for i in self.interactions if not (i.user_id == interaction.user_id and i.book_id == interaction.book_id)
        ]
        self.interactions.append(interaction)

    def forget_user(self, user_id: str) -> bool:
        """Remove a pessoa e as interações dela da memória do serviço."""
        existed = self.users.pop(user_id, None) is not None
        self.interactions = [i for i in self.interactions if i.user_id != user_id]
        return existed
