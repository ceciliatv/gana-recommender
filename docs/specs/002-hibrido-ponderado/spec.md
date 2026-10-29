# 002 — Híbrido ponderado com peso adaptativo

**Status:** Concluída · **Data:** 2026-10-29

## Problema
- `algorithms/hybrid.py:205-235` normaliza cada score dividindo pelo máximo **só entre os 3·n candidatos de cada algoritmo**. Um livro fora do top do colaborativo recebe 0 nesse componente mesmo tendo score positivo, e a escala muda conforme `n`.
- O peso `alpha` é o mesmo para todo usuário (`hybrid.py:197`). Para quem leu dois livros, o colaborativo é ruído; para quem leu cinquenta, o conteúdo desperdiça sinal.
- A similaridade do colaborativo (`collaborative.py:71-75`) é cosseno sobre ratings brutos. Como "Abandonado" vale 1,0 e "Lido" 3,5, abandonar um livro ainda conta como sinal **positivo** de gosto.
- O colaborativo soma a contribuição de **todos** os usuários (`collaborative.py:88`), sem limitar aos vizinhos mais próximos.
- Nenhuma recomendação diz por que foi feita.

## Objetivo
Um híbrido ponderado (Aggarwal, *Recommender Systems: The Textbook*, cap. 6) em que os componentes são comparáveis, o peso se adapta ao histórico de cada pessoa e cada sugestão vem com um motivo.

## Proposta
- **Colaborativo user-based** com os julgamentos ("Lido", "Abandonado" e reviews) **centrados na média do usuário** (cap. 2 do Aggarwal), encolhida para um ponto neutro de 2,5 para não zerar quem tem poucas leituras: abandonar vira sinal negativo. "Lendo" (+0,5) e "Quero ler" (+0,2) não são julgamento e entram com peso fixo positivo; similaridade de cosseno sobre os vetores centrados (equivalente ao Pearson); predição pelos `k=20` vizinhos mais parecidos com similaridade positiva.
- **Conteúdo** com TF-IDF sobre `main_category` (peso 2), `categories` e autores; perfil do usuário = média dos vetores dos livros, ponderada pelo rating centrado.
- **Normalização** dos dois scores em percentil sobre **todos** os candidatos antes de somar.
- **Peso adaptativo:** `alpha_u = α_max · n_u / (n_u + 5)`, com `n_u` = interações do usuário, e a popularidade como prior que some com a evidência (spec 003): `score = alpha_u·colaborativo + (1 − alpha_u − g_u)·conteúdo + g_u·popularidade`. O parâmetro `alpha` da API continua valendo como peso fixo quando enviado (compatibilidade).
- **Motivos** (`reasons`): "leitores com gosto parecido com o seu leram", "mesma categoria de X", "do mesmo autor de Y".

## Escopo
- **Dentro:** os três algoritmos, explicações, compatibilidade do endpoint.
- **Fora:** item-based CF e fatoração de matrizes (o volume de dados do app ainda não pede).

## Critérios de aceite
- [x] Usuário que abandonou um livro não recebe recomendações puxadas por esse livro (`tests/test_recommenders.py`).
- [x] `alpha_u` cresce com o histórico e o híbrido com peso adaptativo não é pior que o melhor peso fixo na avaliação offline (spec 006). Depois da correção: NDCG@10 0,0592 contra 0,0576 do melhor peso fixo.
- [x] Toda recomendação traz `reasons` não vazio.
- [x] `GET /recommend/{user_id}` sem `alpha` usa o peso adaptativo; com `alpha`, usa o valor enviado.

## Clarify
**P1.** Trocar para item-based? *Recomendação:* não agora. Com poucos usuários, user-based com vizinhança é mais fácil de explicar e o ganho do item-based aparece com volume.
**Decisão** User-based com vizinhança e centragem. | 2026-10-29

## Riscos
- Centrar pela média com usuários de uma interação zera o vetor; esses usuários são tratados pelo cold start (spec 003).

## Registro de implementação
- 2026-10-29: a primeira versão centrava também "Lendo" (3,0). No mock, para quem avalia quase tudo com 4 ou 5, "Lendo" ficava abaixo da média e virava rejeição, o que tornava negativa a similaridade entre leitores com gosto parecido. Por isso "Lendo" e "Quero ler" passaram a ter peso fixo.
- 2026-10-29: na primeira avaliação (Goodbooks, 3.000 usuários) o adaptativo `n/(n+5)` **perdeu** para o peso fixo 0,5 no leave-one-out (NDCG@10 0,0516 contra 0,0576). Com ~110 leituras por pessoa, `alpha` ia a 0,96 e o resultado virava colaborativo puro, que nesse dataset é mais fraco que o conteúdo (0,0457 contra 0,0527). O critério 2 desta spec falhou. Correção: teto `α_max` e prior de popularidade, escolhidos numa amostra de validação separada (semente 7, 1.500 usuários): `α_max = 0,3`.
