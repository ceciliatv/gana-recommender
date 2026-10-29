"""
Escolhe a fonte de dados (Supabase real ou mock) e expoe um contrato unico:
get_users() / get_books() / get_interactions().

Como usar o BANCO real (Supabase): defina as variaveis de ambiente
(ver .env.example) e instale as deps (`pip install -r requirements.txt`):

  SUPABASE_URL          = https://<projeto>.supabase.co
  SUPABASE_SERVICE_KEY  = <service_role key>   (server-side; NUNCA versionar)

Usamos a *service_role key* (e nao a publishable/anon) porque o servico le as
tabelas server-side: a anon key da "permission denied" nas tabelas protegidas
por RLS (book_cache, user_book, users). A service_role ignora a RLS.

Sem essas variaveis — ou sem o pacote `supabase`, ou se a conexao falhar —
cai automaticamente no mock, sem quebrar a POC.
"""
from __future__ import annotations
import os

from data import mock_data


def _load_env() -> None:
    """Carrega um .env se o python-dotenv estiver disponivel (opcional)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # variaveis podem vir direto do ambiente


class MockSource:
    """Fonte de dados em memoria (mock_data), para rodar a POC sem banco."""

    def get_users(self):
        return mock_data.get_users()

    def get_books(self):
        return mock_data.get_books()

    def get_interactions(self):
        return list(mock_data.get_interactions())


def build_source():
    """
    Retorna (source, label). Tenta o Supabase; em qualquer falha, usa o mock.
    O `label` descreve a fonte escolhida (util para log na inicializacao).
    """
    _load_env()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        return MockSource(), "mock (defina SUPABASE_URL e SUPABASE_SERVICE_KEY para usar o banco)"

    try:
        from supabase import create_client
        from data.supabase_source import SupabaseSource

        client = create_client(url, key)
        source = SupabaseSource(client)
        source.validate()  # confere acesso a TODAS as tabelas (falha cedo e claro)
        return source, f"Supabase ({url})"
    except Exception as exc:  # rede/credenciais/permissao/pacote ausente
        msg = str(exc)
        if "permission denied" in msg or "42501" in msg:
            hint = getattr(exc, "hint", None) or ""
            print(
                "[ERRO] Sem permissao para ler as tabelas no Supabase.\n"
                "       - Se a chave for a 'anon'/'publishable': troque pela 'service_role'\n"
                "         (ou 'sb_secret_...') no .env em SUPABASE_SERVICE_KEY.\n"
                "       - Se a chave JA for a service_role: o role nao tem GRANT nas\n"
                "         tabelas. Rode no SQL Editor do Supabase:\n"
                "           GRANT SELECT ON public.users, public.book_cache,\n"
                "             public.user_book TO service_role;\n"
                f"       Detalhe do banco: {msg}\n"
                f"       Hint: {hint}\n"
                "       Caindo no mock por enquanto."
            )
        else:
            print(f"[WARN] Falha ao conectar no Supabase ({exc}). Usando mock.")
        return MockSource(), "mock (fallback apos erro de conexao)"


def load_into(source, state) -> None:
    """Carrega os dados da fonte para um objeto de estado (ex.: app.state)."""
    state.users = source.get_users()
    state.books = source.get_books()
    state.interactions = list(source.get_interactions())
