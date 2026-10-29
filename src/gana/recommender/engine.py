"""Motor do Gana: escolhe a estratégia de cada pessoa e mistura os componentes.

Estratégias (specs 002, 003 e 005):

  non_personalized   sem consentimento (ou criança sem consentimento dos pais):
                     popularidade bayesiana, e as leituras dela não treinam nada
  popularity         sem interações e sem gêneros do onboarding
  cold_start_genres  sem interações, com gêneros: (1−γ₀)·conteúdo dos gêneros + γ₀·popularidade
  hybrid             a·colaborativo + (1−a−g)·conteúdo + g·popularidade, com
                     a = 0,3·n/(n+5) e g = 0,5·5/(n+5): a popularidade é um prior que
                     some conforme a pessoa lê, e o colaborativo cresce até 0,3.
                     Com `alpha` explícito (API): a·colaborativo + (1−a)·conteúdo.
                     Com menos de 5 interações, o conteúdo também usa os gêneros do onboarding
  collaborative / content   um componente só, quando pedido explicitamente

Os componentes viram percentis sobre o catálogo inteiro antes de somar, e
livros sensíveis saem para menores e para quem tem idade desconhecida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
from scipy.stats import rankdata

from gana.data.source import DataState
from gana.domain import Book, User
from gana.privacy import is_sensitive, may_personalize, treat_as_minor
from gana.recommender.collaborative import CollaborativeModel, preference_signal
from gana.recommender.content import ContentModel
from gana.recommender.popularity import bayesian_popularity, interaction_counts

# escolhidos numa amostra de validação do Goodbooks (semente 7), separada da de teste;
# ver o registro da spec 003
K_EVIDENCE = 5.0
ALPHA_MAX = 0.3
POP_PRIOR = 0.5
FEW_INTERACTIONS = 5  # abaixo disso, os gêneros do onboarding ainda ajudam o conteúdo
POPULARITY_WEIGHT = 0.05  # desempate, quando o peso vem fixo da API


def blend_weights(n_interactions: int) -> tuple[float, float]:
    """(peso do colaborativo, peso da popularidade) para quem tem n interações."""
    alpha = ALPHA_MAX * n_interactions / (n_interactions + K_EVIDENCE)
    gamma = POP_PRIOR * K_EVIDENCE / (n_interactions + K_EVIDENCE)
    return alpha, gamma


def adaptive_alpha(n_interactions: int) -> float:
    return blend_weights(n_interactions)[0]


def percentile(values: np.ndarray) -> np.ndarray:
    if len(values) == 0:
        return values
    return (rankdata(values, method="average") - 1) / max(len(values) - 1, 1)


@dataclass
class ScoredBook:
    book: Book
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class RecommendationResult:
    user_id: str
    strategy: str
    algorithm: str
    alpha: float | None
    items: list[ScoredBook]


@dataclass
class Scores:
    strategy: str
    alpha: float | None
    final: np.ndarray
    collaborative: np.ndarray | None = None
    supporters: np.ndarray | None = None


class Recommender:
    def __init__(self, state: DataState, today: date | None = None, k_neighbors: int = 20):
        self.state = state
        self.today = today
        self.book_ids = list(state.books)
        self.books = [state.books[b] for b in self.book_ids]
        self.index = {b: i for i, b in enumerate(self.book_ids)}
        # só entra no treino quem pode ser personalizado (consentimento e idade)
        shareable = {uid for uid, user in state.users.items() if may_personalize(user, today)}
        self.training = [i for i in state.interactions if i.user_id in shareable]
        self.collaborative = CollaborativeModel(self.book_ids, self.training, k_neighbors)
        self.content = ContentModel(self.books)
        self.popularity = bayesian_popularity(self.book_ids, self.training)
        self.counts = interaction_counts(self.book_ids, self.training)
        self.sensitive = np.array([is_sensitive(b) for b in self.books], dtype=bool)

    # ---------------------------------------------------------------- scores
    def signal_of(self, user_id: str) -> dict[str, float]:
        interactions = [i for i in self.state.interactions_of(user_id) if i.book_id in self.index]
        return preference_signal(interactions)

    def scores(
        self,
        user: User,
        signal: dict[str, float],
        algorithm: str = "hybrid",
        alpha: float | None = None,
        genres: list[str] | None = None,
    ) -> Scores:
        popularity = percentile(self.popularity)
        if not may_personalize(user, self.today):
            return Scores("non_personalized", None, popularity)
        if not signal:
            genres = genres or user.favorite_genres
            if not genres:
                return Scores("popularity", None, popularity)
            content = percentile(self.content.score(self.content.profile({}, genres)))
            return Scores("cold_start_genres", None, (1 - POP_PRIOR) * content + POP_PRIOR * popularity)

        weights = {self.index[b]: v for b, v in signal.items()}
        if genres is None and len(signal) < FEW_INTERACTIONS:
            genres = user.favorite_genres
        content = percentile(self.content.score(self.content.profile(weights, genres)))
        raw_cf, supporters = self.collaborative.score(signal, exclude_user=user.user_id)
        collaborative = percentile(raw_cf)
        if algorithm == "collaborative":
            strategy, used_alpha = "collaborative", 1.0
            final = collaborative + POPULARITY_WEIGHT * popularity
        elif algorithm == "content":
            strategy, used_alpha = "content", 0.0
            final = content + POPULARITY_WEIGHT * popularity
        elif alpha is not None:
            strategy, used_alpha = "hybrid", alpha
            final = alpha * collaborative + (1 - alpha) * content + POPULARITY_WEIGHT * popularity
        else:
            used_alpha, gamma = blend_weights(len(signal))
            strategy = "hybrid"
            final = used_alpha * collaborative + (1 - used_alpha - gamma) * content + gamma * popularity
        return Scores(strategy, round(used_alpha, 3), final, raw_cf, supporters)

    def allowed_mask(self, user: User | None) -> np.ndarray:
        return ~self.sensitive if treat_as_minor(user, self.today) else np.ones(len(self.books), dtype=bool)

    # ---------------------------------------------------------- recomendação
    def recommend(
        self,
        user_id: str,
        n: int = 5,
        algorithm: str = "hybrid",
        alpha: float | None = None,
        genres: list[str] | None = None,
    ) -> RecommendationResult:
        user = self.state.users[user_id]
        signal = self.signal_of(user_id)
        scores = self.scores(user, signal, algorithm, alpha, genres)
        mask = self.allowed_mask(user)
        for book in signal:
            mask[self.index[book]] = False
        candidates = np.flatnonzero(mask)
        order = candidates[np.argsort(-scores.final[candidates], kind="stable")][:n]
        items = [
            ScoredBook(
                self.books[i],
                round(float(scores.final[i]), 4),
                self._reasons(i, signal, scores, genres or user.favorite_genres),
            )
            for i in order
        ]
        return RecommendationResult(user_id, scores.strategy, algorithm, scores.alpha, items)

    def _reasons(self, idx: int, signal: dict[str, float], scores: Scores, genres: list[str]) -> list[str]:
        book = self.books[idx]
        reasons: list[str] = []
        if scores.strategy in ("non_personalized", "popularity"):
            reasons.append("bem avaliado por leitores do Gana" if self.counts[idx] else "novidade no catálogo")
            return reasons
        if scores.strategy == "cold_start_genres":
            shared = [g for g in genres if g.lower() in {c.lower() for c in [book.main_category, *book.categories]}]
            reasons.append(f"do gênero que você escolheu: {shared[0]}" if shared else "popular entre leitores do Gana")
            return reasons
        if scores.supporters is not None and scores.supporters[idx] > 0 and scores.strategy != "content":
            count = int(scores.supporters[idx])
            who = f"{count} leitores com gosto parecido com o seu gostaram" if count > 1 else None
            reasons.append(who or "1 leitor com gosto parecido com o seu gostou")
        anchor = self._content_anchor(idx, signal)
        if anchor is not None and scores.strategy != "collaborative":
            other = self.books[anchor]
            if set(book.author) & set(other.author):
                reasons.append(f"do mesmo autor de {other.title}")
            elif book.main_category and book.main_category == other.main_category:
                reasons.append(f"mesma categoria de {other.title} ({book.main_category})")
            else:
                shared = sorted(set(book.categories) & set(other.categories))
                if shared:
                    reasons.append(f"tem {shared[0]} em comum com {other.title}")
        return reasons or ["combina com o seu histórico de leitura"]

    def _content_anchor(self, idx: int, signal: dict[str, float]) -> int | None:
        """O livro de que a pessoa gostou que mais se parece com o candidato."""
        liked = [self.index[b] for b, v in signal.items() if v > 0]
        if not liked:
            return None
        sims = np.asarray((self.content.matrix[liked] @ self.content.matrix[idx].T).todense()).ravel()
        best = int(np.argmax(sims))
        return liked[best] if sims[best] > 0 else None

    # --------------------------------------------------------- similares e alta
    def similar(self, google_books_id: str, n: int = 10, user: User | None = None) -> list[ScoredBook]:
        """ "Quem gostou deste também gostou", com conteúdo como complemento e fallback."""
        idx = self.index[google_books_id]
        co = np.zeros(len(self.books))
        readers = {i.user_id for i in self.training if i.book_id == google_books_id}
        for reader in readers:
            signal = preference_signal([i for i in self.training if i.user_id == reader])
            if signal.get(google_books_id, 0) <= 0:
                continue
            for book, value in signal.items():
                if value > 0 and book != google_books_id:
                    co[self.index[book]] += value
        content = self.content.similarity_to(idx)
        final = 0.7 * percentile(co) + 0.3 * percentile(content) if co.any() else percentile(content)
        mask = self.allowed_mask(user)
        mask[idx] = False
        candidates = np.flatnonzero(mask)
        order = candidates[np.argsort(-final[candidates], kind="stable")][:n]
        title = self.books[idx].title
        results = []
        for i in order:
            reasons = []
            if co[i] > 0:
                reasons.append(f"quem gostou de {title} também gostou")
            if set(self.books[i].author) & set(self.books[idx].author):
                reasons.append(f"do mesmo autor de {title}")
            elif self.books[i].main_category == self.books[idx].main_category:
                reasons.append(f"mesma categoria de {title}")
            results.append(ScoredBook(self.books[i], round(float(final[i]), 4), reasons or ["parecido"]))
        return results

    def trending(self, n: int = 10, user: User | None = None) -> list[ScoredBook]:
        mask = self.allowed_mask(user) & (self.counts > 0)
        candidates = np.flatnonzero(mask)
        order = candidates[np.argsort(-self.popularity[candidates], kind="stable")][:n]
        return [
            ScoredBook(self.books[i], round(float(self.popularity[i]), 4), [f"{int(self.counts[i])} leitores no Gana"])
            for i in order
        ]
