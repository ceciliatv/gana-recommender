# 003 — Cold start de usuário e de livro

**Status:** Em andamento · **Data:** 2026-10-29

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
| 1 a 4 interações | híbrido com `alpha_u` baixo (domina o conteúdo) |
| 5 ou mais | híbrido com `alpha_u` adaptativo |

- **Gêneros do onboarding:** coluna `users.favorite_genres` (lida do Supabase) ou parâmetro `genres` na chamada.
- **Popularidade bayesiana:** média ponderada `(v·R + m·C) / (v + m)`, com `v` = interações do livro, `R` = rating médio dele, `C` = média global e `m` = mediana de interações por livro. Livros com pouca evidência puxam para a média.
- **Livro novo:** entra pelo componente de conteúdo, que cobre o catálogo inteiro; o percentil do colaborativo para ele é o mínimo, então ele compete pelo conteúdo.
- A resposta informa a estratégia usada (`strategy`) e cada item traz motivos.

## Escopo
- **Dentro:** camadas, popularidade bayesiana, `favorite_genres`, `/trending` com a nova popularidade.
- **Fora:** perguntas ativas de onboarding (são do app).

## Critérios de aceite
- [ ] Usuário sem interações e com gêneros recebe livros desses gêneros (`tests/test_cold_start.py`).
- [ ] Usuário sem interações e sem gêneros recebe a lista de popularidade bayesiana.
- [ ] Um livro sem nenhuma interação pode aparecer na recomendação de quem lê o mesmo gênero.
- [ ] Na avaliação de cold start (spec 006), a estratégia em camadas supera colaborativo e popularidade pura para usuários com 0 a 3 interações.

## Clarify
**P1.** Onde guardar os gêneros do onboarding? *Recomendação:* coluna `favorite_genres text[]` em `users`, preenchida pelo app; o serviço só lê.
**Decisão** Coluna em `users` + parâmetro `genres` para testes e para o app enviar antes de salvar. | 2026-10-29

## Riscos
- Se o app não preencher `favorite_genres`, o cold start cai em popularidade. A migração e o README documentam o campo.
