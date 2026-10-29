"""
Filtragem Colaborativa baseada em usuários (User-Based Collaborative Filtering).

Ideia: encontra usuários com gostos similares ao usuário-alvo (vizinhos)
e recomenda livros que esses vizinhos gostaram mas o alvo ainda não leu.

Similaridade medida por cosseno sobre os vetores de rating.
"""

import numpy as np
from .base import BaseRecommender
from typing import List


class CollaborativeRecommender(BaseRecommender):

    def fit(self):
        user_ids = [u["user_id"] for u in self.users]
        book_ids = [b["book_id"] for b in self.books]

        self.user_index = {uid: i for i, uid in enumerate(user_ids)}
        self.book_index = {bid: i for i, bid in enumerate(book_ids)}
        self.book_ids = book_ids

        n_users = len(user_ids)
        n_books = len(book_ids)

        self.matrix = np.zeros((n_users, n_books))
        for uid, bid, rating in self.interactions:
            if uid in self.user_index and bid in self.book_index:
                self.matrix[self.user_index[uid]][self.book_index[bid]] = rating

        # similaridade cosseno entre todos os pares de usuários
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        normalized = self.matrix / norms
        self.similarity = normalized @ normalized.T  # (n_users x n_users)

    def recommend(self, user_id: str, n: int = 5) -> List[dict]:
        if user_id not in self.user_index:
            return []

        u_idx = self.user_index[user_id]
        sim_scores = self.similarity[u_idx].copy()
        sim_scores[u_idx] = 0  # exclui o próprio usuário

        already_read = self._already_read(user_id)

        # score ponderado: soma(similaridade * rating) para cada livro
        weighted_scores = sim_scores @ self.matrix  # (n_books,)

        results = []
        for i, bid in enumerate(self.book_ids):
            if bid not in already_read:
                results.append((bid, weighted_scores[i]))

        results.sort(key=lambda x: x[1], reverse=True)
        return [self._format(bid, score) for bid, score in results[:n]]
