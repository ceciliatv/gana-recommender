# LGPD no serviço de recomendação

> Decisões técnicas inspiradas na Lei Geral de Proteção de Dados (Lei 13.709/2018) e no Estatuto da Criança e do Adolescente. Este documento **não é parecer jurídico**; uma versão de produção precisaria da revisão de quem cuida da proteção de dados do produto.

## Inventário: o que o serviço lê

| Dado | Origem | Para quê | Sai do serviço? |
|---|---|---|---|
| `users.id` | Supabase | identificar a pessoa | só pseudonimizado nos logs |
| `users.birth_date` | Supabase | faixa etária (filtro de conteúdo, regra de crianças) | não; só a faixa, na rota do titular |
| `users.personalization_consent`, `parental_consent` | Supabase | decidir se personaliza | na rota do titular |
| `users.favorite_genres` | Supabase / app | cold start | na rota do titular |
| `user_book` (livro, status) | Supabase | sinal de preferência | na rota do titular |
| `book_cache` | Supabase / Google Books | catálogo (dados públicos de livros) | sim |

O serviço **não lê** nome, username, e-mail nem as reviews em texto (**minimização**, art. 6º, III). A rota `GET /users` da POC, que listava nome e username de todo mundo, foi removida.

## Bases legais e regras

- **Personalização por consentimento** (arts. 7º, I e 8º). `personalization_consent` começa desligado. Sem ele:
  - a pessoa recebe recomendações não personalizadas (popularidade, filtrada por idade);
  - as leituras dela não entram no colaborativo de ninguém nem na popularidade.
- **Crianças** (art. 14, §1º). Menores de 12 anos só são personalizados com `parental_consent`.
- **Conteúdo por idade.** Menores de 18 e pessoas com idade desconhecida não recebem livros com `maturityRating = MATURE` (Google Books) nem com categorias sensíveis. Para idade desconhecida, vale o padrão mais protetivo.
- **Revogação.** Quando o consentimento é retirado no app, o próximo `POST /refresh` tira as leituras da pessoa do treino.

## Direitos do titular (art. 18)

| Direito | Como |
|---|---|
| Acesso e portabilidade (II, V) | `GET /users/{id}/data` devolve, em JSON, faixa etária, consentimentos, gêneros e interações |
| Eliminação (VI) | `DELETE /users/{id}/data` remove a pessoa da memória do serviço na hora; a remoção no banco é feita pelo app, dono dos dados |
| Revisão de decisões automatizadas (art. 20) | toda recomendação traz `reasons` e a resposta informa a `strategy` usada |

## Segurança (art. 46)

- Com `SUPABASE_JWT_SECRET` configurado, as rotas por usuário exigem o JWT do Supabase e o `sub` precisa ser o próprio usuário: ninguém consulta a recomendação (e, portanto, os hábitos de leitura) de outra pessoa. Testado em `tests/test_auth.py`.
- A `service_role` key fica só no servidor (`.env`, fora do Git).
- Logs usam `sha256(sal:id)` truncado, nunca o UUID.
- **Limitação conhecida:** projetos Supabase que migraram para chaves de assinatura assimétricas (JWKS) precisam de validação por chave pública; hoje o serviço valida só HS256 com o JWT secret.

## Retenção

O serviço não persiste nada: os dados vivem em memória e são recarregados da fonte. Logs pseudonimizados seguem a política de retenção da infraestrutura onde o serviço roda.
