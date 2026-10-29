"""Tipos do domínio e a regra única de rating implícito."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

Status = Literal["Quero ler", "Lendo", "Lido", "Abandonado"]

# rating implícito pelo status da estante, usado quando não há review com nota
STATUS_RATING: dict[str, float] = {
    "Lido": 3.5,
    "Lendo": 3.0,
    "Quero ler": 2.0,
    "Abandonado": 1.0,
}


@dataclass(frozen=True)
class Book:
    google_books_id: str
    title: str
    author: list[str] = field(default_factory=list)
    main_category: str = ""
    categories: list[str] = field(default_factory=list)
    pages: int = 0
    year_published: int = 0
    url_image: str | None = None
    language: str = "pt"
    maturity_rating: str = "NOT_MATURE"  # "MATURE" ou "NOT_MATURE", do Google Books
    isbn: str | None = None
    publisher: str | None = None

    @property
    def book_id(self) -> str:
        # o app junta livros e interações pelo google_books_id
        return self.google_books_id

    def to_api(self) -> dict:
        return {
            "book_id": self.book_id,
            "google_books_id": self.google_books_id,
            "title": self.title,
            "author": list(self.author),
            "main_category": self.main_category,
            "categories": list(self.categories),
            "pages": self.pages,
            "year_published": self.year_published,
            "url_image": self.url_image,
        }


@dataclass
class User:
    """Só o que o motor precisa (minimização): sem nome, username ou e-mail."""

    user_id: str
    birth_date: date | None = None
    personalization_consent: bool = False
    parental_consent: bool = False
    favorite_genres: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Interaction:
    user_id: str
    book_id: str
    status: Status
    rate: float | None = None  # nota da review (1 a 5), quando existe

    @property
    def rating(self) -> float:
        return self.rate if self.rate is not None else STATUS_RATING[self.status]


def normalize_user_id(user_id: str) -> str:
    """O app iOS envia UUID em maiúsculas; o banco guarda em minúsculas."""
    return user_id.strip().lower()
