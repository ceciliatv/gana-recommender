# Specs do Gana Recommender

O serviço nasceu como uma POC (primeiro commit do repositório) e evoluiu por **spec-driven development**: cada mudança começou como uma spec com problema (apontando arquivo e linha da POC), proposta e critérios de aceite checáveis. O histórico do Git segue a ordem spec → implementação.

## Fluxo

1. **Spec** (`NNN-nome/spec.md`): problema, objetivo, proposta, escopo, critérios de aceite, clarify e riscos.
2. **Clarify**: perguntas com recomendação e resposta registrada ("**Resposta** … | nome, data" quando veio da dona do projeto; "**Decisão** …" quando foi um padrão adotado na implementação).
3. **Tasks** (`tasks.md`), implementação com um commit por spec (`feat(NNN)` / `refactor(NNN)`) e verificação. Só é marcado `[x]` o que foi verificado.

## Índice

| Spec | Assunto | Status |
|---|---|---|
| [001](001-reestruturacao/spec.md) | Reestruturação da POC em pacote, com testes | Em andamento |
| [002](002-hibrido-ponderado/spec.md) | Híbrido ponderado com peso adaptativo | Em andamento |
| [003](003-cold-start/spec.md) | Cold start de usuário e de livro | Em andamento |
| [004](004-google-books/spec.md) | Integração com a Google Books API | Em andamento |
| [005](005-lgpd-e-classificacao-etaria/spec.md) | LGPD e classificação etária | Em andamento |
| [006](006-avaliacao-e-ci/spec.md) | Avaliação offline e CI | Em andamento |
