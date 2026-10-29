"""Autenticação das rotas por usuário com o JWT do Supabase (spec 005).

Com `SUPABASE_JWT_SECRET` configurado, a rota exige `Authorization: Bearer <token>`
e o `sub` do token precisa ser o próprio usuário da rota. Sem a variável
(desenvolvimento local), a checagem fica desligada e o serviço avisa no log.
O caminho coberto por testes é o HS256 com o JWT secret do projeto.
"""

from __future__ import annotations

import jwt
from fastapi import HTTPException, Request

from gana.config import Settings
from gana.domain import normalize_user_id

SUPABASE_AUDIENCE = "authenticated"


def authenticated_subject(request: Request, settings: Settings) -> str | None:
    """Devolve o `sub` do token, ou None quando a autenticação está desligada."""
    if not settings.auth_enabled:
        return None
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "token ausente", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience=SUPABASE_AUDIENCE)
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "token inválido", headers={"WWW-Authenticate": "Bearer"}) from exc
    return normalize_user_id(str(claims.get("sub", "")))


def require_user(request: Request, settings: Settings, user_id: str) -> None:
    subject = authenticated_subject(request, settings)
    if subject is not None and subject != normalize_user_id(user_id):
        raise HTTPException(403, "o token não pertence a este usuário")
