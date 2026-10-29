# 005 — LGPD e classificação etária

**Status:** Em andamento · **Data:** 2026-10-29

> Esta spec descreve decisões técnicas inspiradas na LGPD (Lei 13.709/2018) e no ECA. Não é parecer jurídico.

## Problema
- `GET /users` (`api/routes.py:375`) expõe nome e username de todos os usuários, sem autenticação.
- Qualquer pessoa que saiba um UUID pode pedir as recomendações de outra (`/recommend/{user_id}`), que revelam hábitos de leitura.
- O motor usa as leituras de todo mundo no colaborativo, sem considerar consentimento.
- Não há forma de a pessoa ver o que o motor sabe sobre ela nem de pedir a remoção.
- Um adolescente pode receber livros com conteúdo adulto.

## Objetivo
O serviço trata só os dados de que precisa, só para quem consentiu, protege o acesso, atende aos direitos do titular e filtra conteúdo por idade.

## Proposta
**Minimização (art. 6º, III).** O motor lê de `users` só: `id`, `birth_date`, `personalization_consent`, `parental_consent`, `favorite_genres`. Nome, username e e-mail não entram. `GET /users` sai.

**Consentimento (arts. 7º, I e 8º).** Sem `personalization_consent`:
- a pessoa recebe só recomendações não personalizadas (popularidade, filtrada por idade);
- as leituras dela **não** entram no colaborativo de ninguém.

**Crianças e adolescentes (art. 14 e ECA).**
- Menor de 12 anos: personalização só com `parental_consent`.
- Menor de 18 anos: livros com `maturity_rating = "MATURE"` (Google Books) e categorias sensíveis ficam fora.
- Idade desconhecida: tratada como menor para fins de conteúdo (padrão mais protetivo).

**Direitos do titular (art. 18).**
- `GET /users/{id}/data`: acesso e portabilidade; devolve, em JSON, tudo o que o serviço guarda sobre a pessoa (faixa etária, consentimentos, gêneros, interações).
- `DELETE /users/{id}/data`: eliminação; remove a pessoa da memória do serviço na hora. A remoção no banco é do app (dono dos dados), e a resposta diz isso.
- Toda recomendação traz `reasons`, o que apoia o direito de revisão de decisões automatizadas (art. 20).

**Segurança (art. 46).**
- Com `SUPABASE_JWT_SECRET` configurado, rotas por usuário exigem `Authorization: Bearer <JWT do Supabase>` e o `sub` do token precisa ser o `user_id` da rota. Sem a variável (desenvolvimento), a autenticação fica desligada e o serviço avisa no log.
- Logs com o id pseudonimizado (`sha256` com sal), nunca o UUID puro.

**Documento:** `docs/LGPD.md` com o inventário de dados, bases legais, direitos e retenção.

## Escopo
- **Dentro:** política de idade e consentimento, rotas de titular, JWT, pseudonimização, migração com os campos novos, documento.
- **Fora:** fluxo de consentimento no app (tela e texto), DPO e registro de operações.

## Critérios de aceite
- [ ] Sem consentimento: estratégia `non_personalized` e as leituras da pessoa não alteram o colaborativo de outra (`tests/test_privacy.py`).
- [ ] Menor de 18 e idade desconhecida nunca recebem livro `MATURE`.
- [ ] Menor de 12 sem `parental_consent` recebe não personalizado.
- [ ] `GET /users/{id}/data` devolve os dados da pessoa; `DELETE` remove e a próxima chamada retorna 404.
- [ ] Com `SUPABASE_JWT_SECRET`, token ausente → 401; `sub` diferente → 403; token válido → 200.
- [ ] `GET /users` não existe mais (404).

## Clarify
**P1.** Qual base legal para personalização? *Recomendação:* consentimento, com opção de recusa sem perder o app (recomendações genéricas).
**Decisão** Consentimento, campo `personalization_consent`. | 2026-10-29

**P2.** O que fazer com idade desconhecida? *Recomendação:* tratar como menor só para filtro de conteúdo; não bloquear personalização.
**Decisão** Filtro de conteúdo como menor; personalização segue o consentimento. | 2026-10-29

## Riscos
- `maturityRating` do Google Books é autodeclarado pelas editoras e falha. A lista de categorias sensíveis é uma segunda barreira, não uma garantia.
