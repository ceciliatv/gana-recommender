"""Cria o app FastAPI.

Os dados são carregados uma vez na inicialização (Supabase ou mock) e ficam em
`app.state`. `POST /refresh` recarrega sem reiniciar o serviço.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from gana import __version__
from gana.api.routes import router
from gana.config import Settings, get_settings
from gana.data.source import DataSource, DataState, build_source
from gana.recommender.engine import Recommender

log = logging.getLogger("gana")


def create_app(settings: Settings | None = None, source: DataSource | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings or get_settings()
        if source is None:
            app.state.source, app.state.source_label = build_source(app.state.settings)
        else:
            app.state.source, app.state.source_label = source, type(source).__name__
        app.state.data = DataState.load(app.state.source)
        app.state.engine = Recommender(app.state.data)
        log.info("fonte de dados: %s", app.state.source_label)
        if not app.state.settings.auth_enabled:
            log.warning("SUPABASE_JWT_SECRET ausente: rotas por usuário sem autenticação (só para desenvolvimento)")
        yield

    app = FastAPI(
        title="Gana — API de recomendação",
        description="Motor de recomendação híbrido da rede social de livros Gana.",
        version=__version__,
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
