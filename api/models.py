"""
Modelos Pydantic espelhando o schema real do banco de dados do app Gana.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# ── Responses ──────────────────────────────────────────────────────────────

class BookResponse(BaseModel):
    book_id: str
    google_books_id: str
    title: str
    author: List[str]
    main_category: str
    categories: List[str]
    pages: int
    year_published: int
    url_image: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    username: str
    name: str
    is_private: bool


class RecommendationItem(BaseModel):
    book_id: str
    title: str
    main_category: str
    categories: List[str]
    author: List[str]
    url_image: Optional[str] = None
    score: float


class RecommendationResponse(BaseModel):
    user_id: str
    algorithm: str
    recommendations: List[RecommendationItem]


# ── Requests ───────────────────────────────────────────────────────────────

StatusEnum = Literal["Quero ler", "Lendo", "Lido", "Abandonado"]

class InteractionRequest(BaseModel):
    user_id: str
    book_id: str
    status: StatusEnum
    rate: Optional[float] = Field(
        default=None, ge=1.0, le=5.0,
        description="Avaliação de 1.0 a 5.0 (opcional — vem do Post_Review)"
    )


class InteractionResponse(BaseModel):
    message: str
    user_id: str
    book_id: str
    status: str
    effective_rating: float
