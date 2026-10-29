# 001 — Reestruturação da POC em pacote, com testes

**Status:** Concluída · **Data:** 2026-10-29

## Problema
A POC funciona, mas foi escrita para provar a ideia:
- módulos soltos na raiz (`algorithms/`, `api/`, `data/`, `evaluator.py`) importados por caminho relativo ao diretório atual;
- o mapa de rating implícito existe em dois lugares (`api/routes.py:361` e `data/supabase_source.py:682`) com os mesmos valores copiados;
- nenhum teste; a única verificação é rodar `main.py` e olhar a saída;
- interações circulam como tuplas `(user_id, book_id, rating)`, sem tipo;
- `GET /users` (`api/routes.py:375`) devolve nome e username de todo mundo, o que o motor não precisa.

## Objetivo
Um pacote instalável (`gana`), com tipos explícitos, uma fonte única para regras de negócio e testes automatizados, **sem quebrar o contrato que o app iOS já consome**.

## Proposta
- Layout `src/gana/` com `pyproject.toml` e comando `gana`.
- `gana/domain.py`: `User`, `Book`, `Interaction` (dataclasses) e o mapa único `STATUS_RATING`.
- `gana/data/`: `DataSource` (protocolo), `MockSource` (dados sintéticos, ampliados) e `SupabaseSource` (o da POC, com os campos novos das specs 003 e 005).
- `gana/recommender/`: os três algoritmos com interface comum.
- `gana/api/`: FastAPI com os mesmos caminhos e formatos de resposta usados pelo app (`/recommend/{user_id}`, `/similar/{google_books_id}`, `/trending`, `/books`, `/interactions`, `/refresh`).
- `supabase/migrations/`: o esquema das tabelas que o serviço lê, para subir um ambiente do zero.

## Escopo
- **Dentro:** mover, tipar, testar, manter compatibilidade.
- **Fora:** mudanças de algoritmo (specs 002 e 003).

## Critérios de aceite
- [x] `pip install -e .` e `gana serve` sobem a API.
- [x] Os campos que o app iOS decodifica (`RecommendationResponseDTO`, `RecommendationItemDTO`, `BookDTO`) continuam presentes, com os mesmos nomes (`tests/test_api_contract.py`).
- [x] `STATUS_RATING` definido em um só lugar (`grep -rn "STATUS_RATING\s*[:=]" src/` só encontra `domain.py`).
- [x] `pytest` passa.

## Clarify
**P1.** Onde fica o backend: repositório novo ou pasta no repositório do app? *Recomendação:* repositório novo, a partir da POC, com o README apontando para o app do time.
**Resposta** Repositório novo a partir da POC. | Cecília, 2026-10-29

**P2.** Manter `GET /users`? *Recomendação:* não; o motor não precisa expor dados pessoais (spec 005). O app não usa esse endpoint.
**Decisão** Remover. | 2026-10-29

## Riscos
- O app iOS envia UUID em maiúsculas; a POC normaliza para minúsculas. A normalização precisa continuar.

## Registro de implementação
- 2026-10-29: o critério do grep foi trocado. A versão original buscava a string "Quero ler", que também aparece legitimamente no tipo `StatusEnum` da API e nos pesos de status não julgados do colaborativo (spec 002). O que importa é o mapa de rating existir uma vez só.
