"""Rotas da API. Os caminhos de recomendação são os que o app iOS já chama."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from gana.api.auth import authenticated_subject, require_user
from gana.api.schemas import (
    BookResponse,
    InteractionRequest,
    InteractionResponse,
    RecommendationItem,
    RecommendationResponse,
    UserDataResponse,
)
from gana.data.source import DataState
from gana.domain import Interaction, normalize_user_id
from gana.privacy import age_band, may_personalize, pseudonymize
from gana.recommender.engine import Recommender, ScoredBook

router = APIRouter()
log = logging.getLogger("gana")


def _engine(request: Request) -> Recommender:
    return request.app.state.engine


def _state(request: Request) -> DataState:
    return request.app.state.data


def _rebuild(request: Request) -> None:
    request.app.state.engine = Recommender(_state(request))


def _item(scored: ScoredBook) -> RecommendationItem:
    book = scored.book
    return RecommendationItem(
        book_id=book.book_id,
        title=book.title,
        main_category=book.main_category,
        categories=book.categories,
        author=book.author,
        url_image=book.url_image,
        score=scored.score,
        reasons=scored.reasons,
    )


def _optional_user(request: Request, user_id: str | None):
    if user_id is None:
        return None
    user_id = normalize_user_id(user_id)
    require_user(request, request.app.state.settings, user_id)
    return _state(request).users.get(user_id)


@router.get("/health", tags=["Serviço"])
def health(request: Request) -> dict:
    state = _state(request)
    return {
        "status": "ok",
        "source": request.app.state.source_label,
        "books": len(state.books),
        "interactions": len(state.interactions),
        "auth": request.app.state.settings.auth_enabled,
    }


@router.get("/books", response_model=list[BookResponse], tags=["Catálogo"])
def list_books(request: Request):
    """Catálogo do book_cache (dados públicos de livros)."""
    return [b.to_api() for b in _state(request).books.values()]


@router.get("/trending", response_model=list[BookResponse], tags=["Recomendação"])
def trending(
    request: Request,
    n: int = Query(10, ge=1, le=50),
    user_id: str | None = Query(None, description="Para o filtro de idade; sem ele, o filtro é o de menor"),
):
    """Livros em alta pela popularidade bayesiana (rating médio puxado para a média quando há pouca evidência)."""
    user = _optional_user(request, user_id)
    return [s.book.to_api() for s in _engine(request).trending(n, user)]


@router.get("/similar/{google_books_id}", response_model=list[BookResponse], tags=["Recomendação"])
def similar(
    request: Request,
    google_books_id: str,
    n: int = Query(10, ge=1, le=20),
    user_id: str | None = Query(None, description="Para o filtro de idade; sem ele, o filtro é o de menor"),
):
    """ "Quem gostou deste também gostou", completado por similaridade de conteúdo."""
    if google_books_id not in _state(request).books:
        return []
    user = _optional_user(request, user_id)
    return [s.book.to_api() for s in _engine(request).similar(google_books_id, n, user)]


@router.get("/recommend/{user_id}", response_model=RecommendationResponse, tags=["Recomendação"])
def recommend(
    request: Request,
    user_id: str,
    algorithm: Literal["collaborative", "content", "hybrid"] = Query("hybrid"),
    n: int = Query(5, ge=1, le=50),
    alpha: float | None = Query(None, ge=0.0, le=1.0, description="Peso fixo do colaborativo; vazio = adaptativo"),
    genres: list[str] | None = Query(None, description="Gêneros do onboarding (sobrescreve favorite_genres)"),
):
    user_id = normalize_user_id(user_id)
    require_user(request, request.app.state.settings, user_id)
    if user_id not in _state(request).users:
        raise HTTPException(404, "usuário não encontrado")
    result = _engine(request).recommend(user_id, n, algorithm, alpha, genres)
    log.info(
        "recommend user=%s strategy=%s", pseudonymize(user_id, request.app.state.settings.log_salt), result.strategy
    )
    return RecommendationResponse(
        user_id=user_id,
        algorithm=algorithm,
        strategy=result.strategy,
        alpha=result.alpha,
        recommendations=[_item(s) for s in result.items],
    )


@router.post("/interactions", response_model=InteractionResponse, status_code=201, tags=["Dados"])
def add_interaction(request: Request, body: InteractionRequest):
    """Atualiza em memória a relação usuário-livro (a gravação real é do app, no user_book)."""
    user_id = normalize_user_id(body.user_id)
    require_user(request, request.app.state.settings, user_id)
    state = _state(request)
    if user_id not in state.users:
        raise HTTPException(404, "usuário não encontrado")
    if body.book_id not in state.books:
        raise HTTPException(404, "livro não encontrado")
    interaction = Interaction(user_id, body.book_id, body.status, body.rate)
    state.upsert_interaction(interaction)
    _rebuild(request)
    return InteractionResponse(
        message="Interação registrada.",
        user_id=user_id,
        book_id=body.book_id,
        status=body.status,
        effective_rating=interaction.rating,
    )


@router.post("/refresh", tags=["Dados"])
def refresh(request: Request):
    """Recarrega usuários, livros e interações da fonte (Supabase ou mock)."""
    authenticated_subject(request, request.app.state.settings)  # exige um token válido quando há auth
    request.app.state.data = DataState.load(request.app.state.source)
    _rebuild(request)
    state = _state(request)
    return {"message": "Dados recarregados.", "books": len(state.books), "interactions": len(state.interactions)}


# ------------------------------------------------------------------ titular (LGPD, art. 18)


@router.get("/users/{user_id}/data", response_model=UserDataResponse, tags=["Titular"])
def user_data(request: Request, user_id: str):
    """Acesso e portabilidade: o que o serviço guarda sobre a pessoa."""
    user_id = normalize_user_id(user_id)
    require_user(request, request.app.state.settings, user_id)
    state = _state(request)
    user = state.users.get(user_id)
    if user is None:
        raise HTTPException(404, "usuário não encontrado")
    return UserDataResponse(
        user_id=user_id,
        age_band=age_band(user),
        personalization_consent=user.personalization_consent,
        parental_consent=user.parental_consent,
        favorite_genres=user.favorite_genres,
        interactions=[
            {"book_id": i.book_id, "status": i.status, "rate": i.rate} for i in state.interactions_of(user_id)
        ],
        used_for_recommendations=may_personalize(user),
    )


@router.delete("/users/{user_id}/data", tags=["Titular"])
def delete_user_data(request: Request, user_id: str):
    """Eliminação: remove a pessoa da memória do serviço na hora."""
    user_id = normalize_user_id(user_id)
    require_user(request, request.app.state.settings, user_id)
    if not _state(request).forget_user(user_id):
        raise HTTPException(404, "usuário não encontrado")
    _rebuild(request)
    log.info("dados removidos user=%s", pseudonymize(user_id, request.app.state.settings.log_salt))
    return {
        "message": "Dados removidos do serviço de recomendação.",
        "note": "A remoção definitiva no banco (users, user_book) é feita pelo app, que é o dono dos dados.",
    }
