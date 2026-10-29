# 006 — Avaliação offline e CI

**Status:** Concluída · **Data:** 2026-10-29

## Problema
`evaluator.py` da POC mede leave-one-out nos 8 usuários do mock: os números variam muito a cada mudança e não dizem nada sobre o comportamento com dados reais. Não há avaliação de cold start, que é o caso mais comum numa rede social nova.

## Objetivo
Uma avaliação reproduzível em dados públicos com o mesmo formato do Gana, e um CI que roda testes e lint em cada push.

## Proposta
- **Benchmark:** Goodbooks-10k (CC BY-SA 4.0), adaptado ao esquema do Gana: notas viram status (1 → "Abandonado"; 2 a 5 → "Lido" com a nota como review), tags do Goodreads viram `categories`, e a mais forte vira `main_category`. Amostra de 3.000 usuários com semente fixa.
- **Protocolo 1 — leave-one-out:** um livro bem avaliado (nota ≥ 4) de cada usuário fica escondido; métricas HR@10 e NDCG@10 com ranking completo.
- **Protocolo 2 — cold start:** usuários de teste com só `k ∈ {0, 1, 3}` interações visíveis, mais três gêneros "de onboarding" (as categorias mais frequentes do histórico completo dele); mede se a estratégia em camadas acerta os livros escondidos.
- **Comparações:** popularidade simples, popularidade bayesiana, colaborativo, conteúdo, híbrido com pesos fixos (0,3; 0,5; 0,7) e híbrido adaptativo.
- **Saída:** `reports/offline.md` e `.json`.
- **CI:** GitHub Actions com `ruff` e `pytest` (sem rede).

## Critérios de aceite
- [x] `gana evaluate` baixa o Goodbooks (se faltar), roda os dois protocolos e escreve o relatório.
- [x] Os números do README vêm do relatório gerado, não de estimativa.
- [x] O workflow passa no GitHub (Python 3.12 e 3.13, execução 40952853137).

## Clarify
**P1.** Por que não avaliar com os dados reais do app? *Recomendação:* o banco tem poucas interações e são dados pessoais; para um repositório público, um dataset aberto com o mesmo formato é o certo.
**Decisão** Goodbooks-10k adaptado. | 2026-10-29

## Riscos
- Goodbooks tem notas explícitas; o app tem mais sinais implícitos (status). A conversão nota → status aproxima, mas não reproduz, o comportamento real.

## Registro de implementação
- 2026-10-29: o mapeamento da proposta original mandava nota 2 para "Lendo", que no motor é sinal positivo fixo. Uma nota 2 é um julgamento (não gostou), então passou a ser "Lido" com a nota como review: a centragem a transforma em sinal negativo, como deve ser.
- 2026-10-29: os pesos do motor (`α_max`, `γ₀`) foram escolhidos numa amostra de validação (semente 7, 1.500 usuários), separada da amostra de teste (semente 42) que gera os números do README.
