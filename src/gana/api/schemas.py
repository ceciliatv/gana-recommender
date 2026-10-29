"""Modelos da API.

Os campos que o app iOS decodifica (`RecommendationResponseDTO`,
`RecommendationItemDTO`, `BookDTO`) continuam com os mesmos nomes. Os campos
novos (`strategy`, `alpha`, `reasons`) são adicionais: o `Decodable` do Swift
ignora chaves que não conhece.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    book_id: str
    google_books_id: str
    title: str
    author: list[str]
    main_category: str
    categories: list[str]
    pages: int
    year_published: int
    url_image: str | None = None


class RecommendationItem(BaseModel):
    book_id: str
    title: str
    main_category: str
    categories: list[str]
    author: list[str]
    url_image: str | None = None
    score: float
    reasons: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    user_id: str
    algorithm: str
    strategy: str = Field(description="non_personalized, popularity, cold_start_genres, hybrid, collaborative, content")
    alpha: float | None = Field(default=None, description="Peso do colaborativo usado (só no híbrido)")
    recommendations: list[RecommendationItem]


StatusEnum = Literal["Quero ler", "Lendo", "Lido", "Abandonado"]


class InteractionRequest(BaseModel):
    user_id: str
    book_id: str
    status: StatusEnum
    rate: float | None = Field(default=None, ge=1.0, le=5.0, description="Nota da review, se houver")


class InteractionResponse(BaseModel):
    message: str
    user_id: str
    book_id: str
    status: str
    effective_rating: float


class UserDataResponse(BaseModel):
    """Tudo o que o serviço guarda sobre a pessoa (LGPD, art. 18, II e V)."""

    user_id: str
    age_band: str
    personalization_consent: bool
    parental_consent: bool
    favorite_genres: list[str]
    interactions: list[dict]
    used_for_recommendations: bool
