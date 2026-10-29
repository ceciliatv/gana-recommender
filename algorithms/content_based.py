"""
Filtragem Baseada em Conteúdo (Content-Based Filtering).

Features usadas: main_category (peso 2x) + categories (one-hot) + author (one-hot).
O peso maior em main_category reflete que ela é o sinal mais forte de preferência.
Perfil do usuário = média ponderada pelos ratings dos vetores dos livros lidos.
"""

import numpy as np
from .base import BaseRecommender
from typing import List


class ContentBasedRecommender(BaseRecommender):

    def fit(self):
        all_categories = sorted({cat for b in self.books for cat in b.get("categories", [])})
        all_main = sorted({b["main_category"] for b in self.books})
        all_authors = sorted({a for b in self.books for a in b.get("author", [])})

        # índices: main_category primeiro (peso duplo), depois categories, depois authors
        offset_main = 0
        offset_cat  = len(all_main)
        offset_auth = offset_cat + len(all_categories)
        self.feature_size = offset_auth + len(all_authors)

        self.main_index   = {m: offset_main + i for i, m in enumerate(all_main)}
        self.cat_index    = {c: offset_cat  + i for i, c in enumerate(all_categories)}
        self.author_index = {a: offset_auth + i for i, a in enumerate(all_authors)}

        self.book_ids = [b["book_id"] for b in self.books]

        self.book_vectors = {}
        for b in self.books:
            vec = np.zeros(self.feature_size)
            # main_category com peso 2 para ter mais influência que as demais categorias
            if b["main_category"] in self.main_index:
                vec[self.main_index[b["main_category"]]] = 2.0
            for cat in b.get("categories", []):
                if cat in self.cat_index:
                    vec[self.cat_index[cat]] = 1.0
            for author in b.get("author", []):
                if author in self.author_index:
                    vec[self.author_index[author]] = 1.0
            self.book_vectors[b["book_id"]] = vec

        self.user_profiles = {}
        for u in self.users:
            uid = u["user_id"]
            rated = [(bid, r) for (u2, bid, r) in self.interactions if u2 == uid]
            if not rated:
                self.user_profiles[uid] = np.zeros(self.feature_size)
                continue
            profile = np.zeros(self.feature_size)
            total_weight = 0.0
            for bid, rating in rated:
                if bid in self.book_vectors:
                    profile += rating * self.book_vectors[bid]
                    total_weight += rating
            self.user_profiles[uid] = profile / total_weight if total_weight else profile

    def recommend(self, user_id: str, n: int = 5) -> List[dict]:
        if user_id not in self.user_profiles:
            return []

        profile = self.user_profiles[user_id]
        already_read = self._already_read(user_id)

        scores = []
        for bid, vec in self.book_vectors.items():
            if bid in already_read:
                continue
            norm = np.linalg.norm(profile) * np.linalg.norm(vec)
            similarity = float(np.dot(profile, vec) / norm) if norm > 0 else 0.0
            scores.append((bid, similarity))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [self._format(bid, score) for bid, score in scores[:n]]
