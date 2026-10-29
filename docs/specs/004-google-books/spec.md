# 004 — Integração com a Google Books API

**Status:** Concluída, com um critério não verificado (ver abaixo) · **Data:** 2026-10-29

## Problema
O motor só conhece os livros que já estão no `book_cache`, que hoje é preenchido pelo app. Não há como popular o catálogo pelo backend, e a classificação etária (spec 005) precisa do campo `maturityRating`, que o app não grava.

## Objetivo
Um cliente da Google Books API que busca e normaliza livros para o formato do `book_cache`, com cache, tratamento de cota e um comando de ingestão.

## Proposta
- `gana/google_books.py`:
  - `search(query, lang=None, max_results=20)` e `get(volume_id)`;
  - `normalize(volume) -> Book`: ISBN-13 (ou 10), autores, páginas, ano, editora, `main_category` (primeiro nível de `categories`, ex.: "Fiction / Fantasy" → "Fiction"), categorias achatadas sem repetição, idioma, capa em `https`, `maturity_rating`;
  - chave opcional `GOOGLE_BOOKS_API_KEY` (a cota anônima é compartilhada e acaba rápido);
  - erro 429/5xx: até 3 tentativas com espera exponencial; depois, erro claro;
  - cache em memória por consulta, com TTL, para não repetir chamadas.
- `gana ingest "consulta"`: busca, normaliza e faz *upsert* no `book_cache` (Supabase) ou imprime o resultado (`--dry-run`).
- **Testes sem rede:** fixtures no formato oficial do recurso `volume`, montadas à mão com metadados públicos (sem sinopses, que têm direito autoral), e `httpx.MockTransport`.

## Escopo
- **Dentro:** cliente, normalização, retentativa, cache, ingestão.
- **Fora:** sincronização periódica, imagens em alta resolução.

## Critérios de aceite
- [x] `normalize` cobre ISBN-13, ISBN-10, livro sem categoria, ano só com "AAAA" e capa `http` → `https` (`tests/test_google_books.py`).
- [x] 429 seguido de 200 resulta em sucesso após nova tentativa; três 429 seguidos geram `GoogleBooksError`.
- [x] A segunda busca igual não faz nova requisição (cache).
- [ ] `gana ingest "torto arado" --dry-run` imprime os livros normalizados quando há cota ou chave. **Não verificado:** sem chave, a API respondeu 429 e o comando mostrou o erro esperado ("cota esgotada: configure GOOGLE_BOOKS_API_KEY").

## Clarify
**P1.** Gravar a sinopse (`description`) no `book_cache`? *Recomendação:* sim no banco (o app já mostra), mas nunca em fixtures ou dados versionados no repositório público.
**Decisão** Sinopse só em tempo de execução. | 2026-10-29

## Riscos
- Durante o desenvolvimento a cota anônima retornou 429; por isso o cliente aceita chave e os testes não dependem da rede.
