# 003 — Cold start de usuário e de livro

**Status:** Concluída, com um critério não atingido (ver abaixo) · **Data:** 2026-10-29

## Problema
- Usuário novo, sem nenhuma interação, recebe lista vazia do colaborativo e do conteúdo (`collaborative.py:78`, `content_based.py:148`); o app cai num mock local.
- Livro novo no `book_cache`, sem interações, nunca aparece no colaborativo, e no híbrido só aparece se estiver no top 3·n do conteúdo.
- O "em alta" (`api/routes.py:391`) conta interações sem considerar a nota nem o tamanho da amostra: um livro com uma interação "Quero ler" empata com um lido e bem avaliado.

## Objetivo
Toda pessoa recebe recomendações úteis desde o primeiro acesso, e livros novos podem ser recomendados.

## Proposta
Estratégia em camadas, escolhida por usuário (*switching hybrid*, Aggarwal cap. 6):

| Situação | Estratégia |
|---|---|
| 0 interações, com gêneros do onboarding | conteúdo a partir dos gêneros escolhidos + popularidade bayesiana |
| 0 interações, sem gêneros | popularidade bayesiana |
| 1 a 4 interações | híbrido com `alpha_u` baixo (domina o conteúdo); o conteúdo usa o histórico **e** os gêneros do onboarding |
| 5 ou mais | híbrido com `alpha_u` adaptativo |

- **Gêneros do onboarding:** coluna `users.favorite_genres` (lida do Supabase) ou parâmetro `genres` na chamada.
- **Popularidade bayesiana:** `log(1 + v) · (v·R + m·C) / (v + m)`, com `v` = interações do livro, `R` = rating médio dele, `C` = média global e `m` = mediana de interações por livro. A média bayesiana puxa para a média os livros com pouca evidência, e o `log(1 + v)` dá peso ao volume.
- **Livro novo:** entra pelo componente de conteúdo, que cobre o catálogo inteiro; o percentil do colaborativo para ele é o mínimo, então ele compete pelo conteúdo.
- A resposta informa a estratégia usada (`strategy`) e cada item traz motivos.

## Escopo
- **Dentro:** camadas, popularidade bayesiana, `favorite_genres`, `/trending` com a nova popularidade.
- **Fora:** perguntas ativas de onboarding (são do app).

## Critérios de aceite
- [x] Usuário sem interações e com gêneros recebe livros desses gêneros (`tests/test_cold_start.py`).
- [x] Usuário sem interações e sem gêneros recebe a lista de popularidade bayesiana.
- [x] Um livro sem nenhuma interação pode aparecer na recomendação de quem lê o mesmo gênero.
- [ ] Na avaliação de cold start (spec 006), a estratégia em camadas supera colaborativo e popularidade pura para usuários com 0 a 3 interações. **Não atingido:** supera com 3 interações (Recall@20 0,2485 contra 0,2403), mas perde para a popularidade pura com 0 (0,2331 contra 0,2454) e 1 (0,2264 contra 0,2437).

## Clarify
**P1.** Onde guardar os gêneros do onboarding? *Recomendação:* coluna `favorite_genres text[]` em `users`, preenchida pelo app; o serviço só lê.
**Decisão** Coluna em `users` + parâmetro `genres` para testes e para o app enviar antes de salvar. | 2026-10-29

## Riscos
- Se o app não preencher `favorite_genres`, o cold start cai em popularidade. A migração e o README documentam o campo.

## Registro de implementação
- 2026-10-29: a primeira versão usava só a média bayesiana. No leave-one-out com 1.000 usuários do Goodbooks ela teve NDCG@10 de 0,0005 (contagem pura: 0,0296), porque mede qualidade e não chance de leitura. Com `log(1 + v)` multiplicando, chegou a 0,0341. Também testado `m` no percentil 90: mesmo resultado com o log, pior sem ele.
- 2026-10-29: com menos de 5 interações, o conteúdo passou a somar os gêneros do onboarding ao histórico (antes eles só valiam com 0 interações).
- 2026-10-29: na primeira avaliação a estratégia em camadas **perdeu** para a popularidade pura com 0 e 1 interação (Recall@20 0,213 contra 0,245 com k=0). No Goodbooks, livros populares dominam todas as estantes e os "gêneros do onboarding" (categorias amplas como Young Adult ou Classics) puxavam para livros menos lidos. Correção: a popularidade virou um prior `g = γ₀·5/(n+5)` que some conforme a pessoa lê. Na validação (semente 7), `γ₀` de 0 a 0,7 levou o recall do cold start de 0,161 a 0,243; escolhido `γ₀ = 0,5` (0,235): 0,7 rendia 3% a mais, mas deixava os gêneros escolhidos no onboarding quase sem efeito na tela, e o leave-one-out ficou igual (dentro do ruído).
