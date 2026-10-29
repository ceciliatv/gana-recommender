"""
Algoritmo Híbrido: combina Collaborative + Content-Based com pesos ajustáveis.

Útil para suavizar as fraquezas de cada abordagem:
- Collaborative sofre com cold start (usuário sem histórico)
- Content-Based fica preso no mesmo tipo de conteúdo (serendipidade baixa)

O peso `alpha` controla o balanço: 0.0 = só content, 1.0 = só collaborative.
"""

from .base import BaseRecommender
from .collaborative import CollaborativeRecommender
from .content_based import ContentBasedRecommender
from typing import List


class HybridRecommender(BaseRecommender):

    def __init__(self, users, books, interactions, alpha: float = 0.5):
        super().__init__(users, books, interactions)
        self.alpha = alpha  # peso do collaborative (1-alpha = content-based)
        self._collab = CollaborativeRecommender(users, books, interactions)
        self._content = ContentBasedRecommender(users, books, interactions)

    def fit(self):
        self._collab.fit()
        self._content.fit()

    def recommend(self, user_id: str, n: int = 5) -> List[dict]:
        # busca mais candidatos para ter margem ao combinar
        k = n * 3

        collab_recs = {r["book_id"]: r["score"] for r in self._collab.recommend(user_id, k)}
        content_recs = {r["book_id"]: r["score"] for r in self._content.recommend(user_id, k)}

        # normaliza scores para [0, 1] antes de combinar
        def normalize(scores: dict) -> dict:
            if not scores:
                return {}
            max_s = max(scores.values()) or 1
            return {bid: s / max_s for bid, s in scores.items()}

        collab_norm = normalize(collab_recs)
        content_norm = normalize(content_recs)

        all_books = set(collab_norm) | set(content_norm)
        already_read = self._already_read(user_id)

        combined = []
        for bid in all_books:
            if bid in already_read:
                continue
            c_score = collab_norm.get(bid, 0.0)
            cb_score = content_norm.get(bid, 0.0)
            final = self.alpha * c_score + (1 - self.alpha) * cb_score
            combined.append((bid, final))

        combined.sort(key=lambda x: x[1], reverse=True)
        return [self._format(bid, score) for bid, score in combined[:n]]
