"""CLI `gana`: servir a API, avaliar o motor e popular o catálogo."""

from __future__ import annotations

from pathlib import Path

import typer

from gana.config import get_settings

app = typer.Typer(help="Gana Recommender.", no_args_is_help=True)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Sobe a API. Para o app no iPhone, use --host 0.0.0.0."""
    import uvicorn

    uvicorn.run("gana.api.app:app", host=host, port=port, reload=reload)


@app.command()
def evaluate(
    users: int = typer.Option(3000, help="Usuários amostrados do Goodbooks-10k."),
    data_dir: Path = typer.Option(Path("data"), help="Onde o Goodbooks-10k é baixado."),
    out_dir: Path = typer.Option(Path("reports"), help="Onde o relatório é escrito."),
) -> None:
    """Avaliação offline (leave-one-out e cold start) no Goodbooks-10k adaptado ao esquema do Gana."""
    from gana.evaluation.offline import run

    run(data_dir, out_dir, n_users=users, log=typer.echo)


@app.command()
def ingest(
    query: str,
    lang: str | None = typer.Option(None, help="Ex.: pt"),
    max_results: int = typer.Option(20, max=40),
    dry_run: bool = typer.Option(False, "--dry-run", help="Só imprime, não grava no Supabase."),
) -> None:
    """Busca livros na Google Books API e grava no book_cache."""
    from gana.google_books import GoogleBooksClient, GoogleBooksError

    settings = get_settings()
    try:
        volumes = GoogleBooksClient(settings.google_books_api_key).search(query, lang, max_results)
    except GoogleBooksError as exc:
        typer.secho(str(exc), fg="red")
        raise typer.Exit(1) from exc
    for v in volumes:
        b = v.book
        flag = " [MATURE]" if b.maturity_rating == "MATURE" else ""
        typer.echo(f"{b.google_books_id}  {b.title} — {', '.join(b.author)} ({b.year_published}) {b.categories}{flag}")
    if dry_run or not volumes:
        return
    if not settings.supabase_url or not settings.supabase_service_key:
        typer.secho("SUPABASE_URL e SUPABASE_SERVICE_KEY são necessárias para gravar.", fg="red")
        raise typer.Exit(1)
    from supabase import create_client

    from gana.data.supabase_source import SupabaseSource

    source = SupabaseSource(create_client(settings.supabase_url, settings.supabase_service_key))
    source.upsert_books([v.book for v in volumes], {v.book.google_books_id: v.description or "" for v in volumes})
    typer.echo(f"{len(volumes)} livros gravados no book_cache.")


if __name__ == "__main__":
    app()
