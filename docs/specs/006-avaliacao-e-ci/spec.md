# 006 — Avaliação offline e CI

**Status:** Em andamento · **Data:** 2026-10-29

## Problema
`evaluator.py` da POC mede leave-one-out nos 8 usuários do mock: os números variam muito a cada mudança e não dizem nada sobre o comportamento com dados reais. Não há avaliação de cold start, que é o caso mais comum numa rede social nova.

## Objetivo
Uma avaliação reproduzível em dados públicos com o mesmo formato do Gana, e um CI que roda testes e lint em cada push.

## Proposta
- **Benchmark:** Goodbooks-10k (CC BY-SA 4.0), adaptado ao esquema do Gana: notas viram status (5–4 → "Lido" com a nota como review, 3 → "Lido", 2 → "Lendo", 1 → "Abandonado"), tags do Goodreads viram `categories`, e a mais forte vira `main_category`. Amostra de 3.000 usuários com semente fixa.
- **Protocolo 1 — leave-one-out:** um livro bem avaliado (nota ≥ 4) de cada usuário fica escondido; métricas HR@10 e NDCG@10 com ranking completo.
- **Protocolo 2 — cold start:** usuários de teste com só `k ∈ {0, 1, 3}` interações visíveis, mais três gêneros "de onboarding" (as categorias mais frequentes do histórico completo dele); mede se a estratégia em camadas acerta os livros escondidos.
- **Comparações:** popularidade simples, popularidade bayesiana, colaborativo, conteúdo, híbrido com pesos fixos (0,3; 0,5; 0,7) e híbrido adaptativo.
- **Saída:** `reports/offline.md` e `.json`.
- **CI:** GitHub Actions com `ruff` e `pytest` (sem rede).

## Critérios de aceite
- [ ] `gana evaluate` baixa o Goodbooks (se faltar), roda os dois protocolos e escreve o relatório.
- [ ] Os números do README vêm do relatório gerado, não de estimativa.
- [ ] O workflow passa no GitHub.

## Clarify
**P1.** Por que não avaliar com os dados reais do app? *Recomendação:* o banco tem poucas interações e são dados pessoais; para um repositório público, um dataset aberto com o mesmo formato é o certo.
**Decisão** Goodbooks-10k adaptado. | 2026-10-29

## Riscos
- Goodbooks tem notas explícitas; o app tem mais sinais implícitos (status). A conversão nota → status aproxima, mas não reproduz, o comportamento real.
