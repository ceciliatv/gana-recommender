"""
Cria e configura o app FastAPI.
Os dados sao carregados uma vez na inicializacao (do Supabase ou do mock) e
ficam em `app.state`, evitando recarregar a cada requisicao. Use POST /refresh
para recarregar da fonte sem reiniciar o servico.
"""

from fastapi import FastAPI
from data.source import build_source, load_into
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gana - API de Recomendacao",
        description="POC do algoritmo de recomendacao de livros para a rede social Gana.",
        version="0.2.0",
    )

    # escolhe a fonte (Supabase se houver credenciais; senao, mock)
    source, label = build_source()
    app.state.source = source
    print(f"[Gana API] Fonte de dados: {label}")

    # carrega os dados uma vez na inicializacao
    load_into(source, app.state)

    app.include_router(router)

    return app


app = create_app()
