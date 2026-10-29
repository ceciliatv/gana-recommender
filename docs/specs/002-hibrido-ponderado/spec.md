# 002 — Híbrido ponderado com peso adaptativo

**Status:** Em andamento · **Data:** 2026-10-29

## Problema
- `algorithms/hybrid.py:205-235` normaliza cada score dividindo pelo máximo **só entre os 3·n candidatos de cada algoritmo**. Um livro fora do top do colaborativo recebe 0 nesse componente mesmo tendo score positivo, e a escala muda conforme `n`.
- O peso `alpha` é o mesmo para todo usuário (`hybrid.py:197`). Para quem leu dois livros, o colaborativo é ruído; para quem leu cinquenta, o conteúdo desperdiça sinal.
- A similaridade do colaborativo (`collaborative.py:71-75`) é cosseno sobre ratings brutos. Como "Abandonado" vale 1,0 e "Lido" 3,5, abandonar um livro ainda conta como sinal **positivo** de gosto.
- O colaborativo soma a contribuição de **todos** os usuários (`collaborative.py:88`), sem limitar aos vizinhos mais próximos.
- Nenhuma recomendação diz por que foi feita.

## Objetivo
Um híbrido ponderado (Aggarwal, *Recommender Systems: The Textbook*, cap. 6) em que os componentes são comparáveis, o peso se adapta ao histórico de cada pessoa e cada sugestão vem com um motivo.

## Proposta
- **Colaborativo user-based** com ratings **centrados na média do usuário** (cap. 2 do Aggarwal): abandonar vira sinal negativo; similaridade de cosseno sobre os vetores centrados (equivalente ao Pearson); predição pelos `k=20` vizinhos mais parecidos com similaridade positiva.
- **Conteúdo** com TF-IDF sobre `main_category` (peso 2), `categories` e autores; perfil do usuário = média dos vetores dos livros, ponderada pelo rating centrado.
- **Normalização** dos dois scores em percentil sobre **todos** os candidatos antes de somar.
- **Peso adaptativo:** `alpha_u = n_u / (n_u + k_alpha)`, com `k_alpha = 5` e `n_u` = interações do usuário. O parâmetro `alpha` da API continua valendo como peso fixo quando enviado (compatibilidade).
- **Motivos** (`reasons`): "leitores com gosto parecido com o seu leram", "mesma categoria de X", "do mesmo autor de Y".

## Escopo
- **Dentro:** os três algoritmos, explicações, compatibilidade do endpoint.
- **Fora:** item-based CF e fatoração de matrizes (o volume de dados do app ainda não pede).

## Critérios de aceite
- [ ] Usuário que abandonou um livro não recebe recomendações puxadas por esse livro (`tests/test_recommenders.py`).
- [ ] `alpha_u` cresce com o histórico e o híbrido com peso adaptativo não é pior que o melhor peso fixo na avaliação offline (spec 006).
- [ ] Toda recomendação traz `reasons` não vazio.
- [ ] `GET /recommend/{user_id}` sem `alpha` usa o peso adaptativo; com `alpha`, usa o valor enviado.

## Clarify
**P1.** Trocar para item-based? *Recomendação:* não agora. Com poucos usuários, user-based com vizinhança é mais fácil de explicar e o ganho do item-based aparece com volume.
**Decisão** User-based com vizinhança e centragem. | 2026-10-29

## Riscos
- Centrar pela média com usuários de uma interação zera o vetor; esses usuários são tratados pelo cold start (spec 003).
