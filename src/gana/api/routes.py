"""
Rotas da API. Cada função é um endpoint que o app iOS vai chamar.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Literal

from algorithms.collaborative import CollaborativeRecommender
from algorithms.content_based import ContentBasedRecommender
from algorithms.hybrid import HybridRecommender
from .models import (
    BookResponse, UserResponse,
    RecommendationResponse, RecommendationItem,
    InteractionRequest, InteractionResponse,
)

router = APIRouter()

ALGORITHM_MAP = {
    "collaborative": CollaborativeRecommender,
    "content":       ContentBasedRecommender,
    "hybrid":        HybridRecommender,
}

_IMPLICIT_RATING = {
    "Lido":       3.5,
    "Lendo":      3.0,
    "Quero ler":  2.0,
    "Abandonado": 1.0,
}


def _state(request: Request):
    return request.app.state


# ── GET /users ───────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse], tags=["Dados"])
def list_users(request: Request):
    """Retorna todos os usuários cadastrados."""
    return _state(request).users


# ── GET /books ───────────────────────────────────────────────────────────────

@router.get("/books", response_model=list[BookResponse], tags=["Dados"])
def list_books(request: Request):
    """Retorna o catálogo de livros do book_cache."""
    return _state(request).books


# ── GET /trending ─────────────────────────────────────────────────────────────

@router.get("/trending", response_model=list[BookResponse], tags=["Dados"])
def trending(
    request: Request,
    n: int = Query(default=10, ge=1, le=50, description="Quantidade de livros"),
):
    """
    Livros em alta = os que tiveram MAIS interações (registros em `user_book`),
    somando todos os usuários. Ordena por contagem desc e devolve os top N
    com os metadados completos do `book_cache`.
    """
    from collections import Counter

    state = _state(request)
    counts = Counter(book_id for (_uid, book_id, _rating) in state.interactions)
    book_map = {b["book_id"]: b for b in state.books}

    ranked = [book_map[bid] for bid, _ in counts.most_common() if bid in book_map]
    return ranked[:n]


# ── GET /similar/{google_books_id} ───────────────────────────────────────────

@router.get("/similar/{google_books_id}", response_model=list[BookResponse], tags=["Recomendação"])
def similar(
    google_books_id: str,
    request: Request,
    n: int = Query(default=10, ge=1, le=20, description="Quantidade de sugestões"),
):
    """
    Recomendação item-a-item ("quem leu este livro também leu ..."):
    1. acha os usuários que interagiram com o livro alvo;
    2. soma os ratings dos OUTROS livros que esses usuários também leram;
    3. devolve os mais pontuados (do book_cache), exceto o próprio livro.

    Devolve lista vazia quando não há co-ocorrência (o app cai no fallback de
    conteúdo, por autor/gênero, via Google Books).
    """
    from collections import defaultdict

    state = _state(request)
    readers = {uid for (uid, bid, _r) in state.interactions if bid == google_books_id}
    if not readers:
        return []

    scores: dict[str, float] = defaultdict(float)
    for (uid, bid, rating) in state.interactions:
        if uid in readers and bid != google_books_id:
            scores[bid] += rating

    book_map = {b["book_id"]: b for b in state.books}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [book_map[bid] for bid, _ in ranked if bid in book_map][:n]


# ── GET /recommend/{user_id} ─────────────────────────────────────────────────

@router.get("/recommend/{user_id}", response_model=RecommendationResponse, tags=["Recomendação"])
def recommend(
    user_id: str,
    request: Request,
    algorithm: Literal["collaborative", "content", "hybrid"] = Query(
        default="hybrid",
        description="Algoritmo: collaborative | content | hybrid"
    ),
    n: int = Query(default=5, ge=1, le=50, description="Quantidade de recomendações"),
    alpha: float = Query(
        default=0.5, ge=0.0, le=1.0,
        description="Peso do collaborative no hybrid (0=só content, 1=só collaborative)"
    ),
):
    """
    Retorna N recomendações de livros do book_cache para o usuário.

    Algoritmos disponíveis:
    - **collaborative**: recomenda com base em usuários com histórico similar
    - **content**: recomenda com base em mainCategory/categories dos livros lidos
    - **hybrid**: combina os dois (controle fino via `alpha`)
    """
    state = _state(request)

    # UUIDs do Supabase sao minusculos; o app iOS envia em maiusculas.
    user_id = user_id.lower()

    if not any(u["user_id"] == user_id for u in state.users):
        raise HTTPException(status_code=404, detail=f"Usuário '{user_id}' não encontrado.")

    cls = ALGORITHM_MAP[algorithm]
    kwargs = {"alpha": alpha} if algorithm == "hybrid" else {}

    model = cls(state.users, state.books, state.interactions, **kwargs)
    model.fit()
    recs = model.recommend(user_id, n)

    # enriquece a resposta com dados completos do book_cache
    book_map = {b["book_id"]: b for b in state.books}
    items = []
    for r in recs:
        b = book_map.get(r["book_id"], {})
        items.append(RecommendationItem(
            book_id=r["book_id"],
            title=r["title"],
            main_category=b.get("main_category", ""),
            categories=b.get("categories", []),
            author=b.get("author", []),
            url_image=b.get("url_image"),
            score=r["score"],
        ))

    return RecommendationResponse(user_id=user_id, algorithm=algorithm, recommendations=items)


# ── POST /interactions ───────────────────────────────────────────────────────

@router.post("/interactions", response_model=InteractionResponse, tags=["Dados"], status_code=201)
def add_interaction(body: InteractionRequest, request: Request):
    """
    Registra ou atualiza a relação de um usuário com um livro.
    Espelha o que acontece quando o app atualiza `user_book` + (opcionalmente) `Post_Review`.

    O rating efetivo é:
      - `rate` da review, se fornecido
      - rating implícito pelo status caso contrário
    """
    state = _state(request)

    # normaliza o UUID (o app iOS envia em maiusculas; o banco guarda minusculo)
    user_id = body.user_id.lower()
    book_id = body.book_id

    if not any(u["user_id"] == user_id for u in state.users):
        raise HTTPException(status_code=404, detail=f"Usuário '{user_id}' não encontrado.")

    if not any(b["book_id"] == book_id for b in state.books):
        raise HTTPException(status_code=404, detail=f"Livro '{book_id}' não encontrado.")

    effective_rating = body.rate if body.rate is not None else _IMPLICIT_RATING[body.status]

    # atualiza em memória (what-if). A persistencia real e feita pelo app no
    # Supabase (user_book); use POST /refresh para recarregar da fonte.
    state.interactions = [
        (u, b, r) for (u, b, r) in state.interactions
        if not (u == user_id and b == book_id)
    ]
    state.interactions.append((user_id, book_id, effective_rating))

    return InteractionResponse(
        message="Interação registrada com sucesso.",
        user_id=user_id,
        book_id=book_id,
        status=body.status,
        effective_rating=effective_rating,
    )


# ── POST /refresh ─────────────────────────────────────────────────────────────

@router.post("/refresh", tags=["Dados"])
def refresh(request: Request):
    """
    Recarrega usuarios, livros e interacoes da fonte (Supabase ou mock) sem
    reiniciar o servico. Util depois que o app grava novos `user_book` no banco.
    """
    from data.source import load_into

    app = request.app
    load_into(app.state.source, app.state)
    state = _state(request)
    return {
        "message": "Dados recarregados da fonte.",
        "users": len(state.users),
        "books": len(state.books),
        "interactions": len(state.interactions),
    }
