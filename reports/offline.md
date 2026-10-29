# Avaliação offline do motor do Gana

Goodbooks-10k adaptado ao esquema do Gana: 3000 usuários amostrados (semente 42), 10000 livros, 336949 interações. Ranking completo, sem amostrar negativos.

## Leave-one-out (2999 usuários)

| Estratégia | HR@10 | NDCG@10 |
|---|---:|---:|
| popularidade (contagem) | 0.0634 | 0.0358 |
| popularidade bayesiana | 0.0574 | 0.0344 |
| colaborativo | 0.0714 | 0.0457 |
| conteúdo | 0.0847 | 0.0527 |
| híbrido α=0,3 | 0.0924 | 0.0575 |
| híbrido α=0,5 | 0.0937 | 0.0576 |
| híbrido α=0,7 | 0.0904 | 0.0567 |
| híbrido adaptativo (Gana) | 0.0927 | **0.0592** |

## Cold start (500 usuários de teste)

Recall@20 com só k interações visíveis e três gêneros de onboarding.

| Estratégia | k=0 | k=1 | k=3 |
|---|---:|---:|---:|
| popularidade (contagem) | 0.2454 | 0.2437 | 0.2403 |
| popularidade bayesiana | 0.2418 | 0.2400 | 0.2375 |
| colaborativo | — | 0.2238 | 0.2401 |
| conteúdo só do histórico | 0.2418 | 0.1579 | 0.2114 |
| em camadas (Gana) | 0.2331 | 0.2264 | 0.2485 |
