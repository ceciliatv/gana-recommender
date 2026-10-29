"""Configuração lida do ambiente (e de um `.env`, se existir). Nenhum segredo no código."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_service_key: str | None
    supabase_jwt_secret: str | None  # liga a autenticação das rotas por usuário
    google_books_api_key: str | None
    log_salt: str

    @property
    def auth_enabled(self) -> bool:
        return bool(self.supabase_jwt_secret)


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        supabase_url=os.getenv("SUPABASE_URL") or None,
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY") or None,
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET") or None,
        google_books_api_key=os.getenv("GOOGLE_BOOKS_API_KEY") or None,
        log_salt=os.getenv("GANA_LOG_SALT") or "gana-dev-salt",
    )
