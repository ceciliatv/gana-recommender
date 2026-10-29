"""Filtragem colaborativa user-based com ratings centrados (Aggarwal, cap. 2).

Mudanças em relação à POC:
- só os julgamentos ("Lido", "Abandonado" e reviews com nota) são centrados na
  média do usuário, encolhida para um ponto neutro (2,5). Assim "Abandonado"
  vira sinal negativo e quem só marcou "Lido" ainda tem um vetor diferente de
  zero. "Lendo" e "Quero ler" não são julgamento: entram com um peso positivo
  fixo e pequeno, senão quem avalia tudo com nota alta veria "Lendo" como rejeição;
- similaridade de cosseno sobre os vetores centrados (equivalente ao Pearson);
- predição só com os k vizinhos de similaridade positiva.
"""

from __future__ import annotations

import numpy as np

from gana.domain import Interaction

NEUTRAL = 2.5  # ponto neutro da escala (entre "Quero ler" e "Lendo")
SHRINK = 2.0  # quantas "interações" de peso o ponto neutro ganha no centro do usuário
UNJUDGED = {"Lendo": 0.5, "Quero ler": 0.2}  # sinal positivo fixo, sem centragem


def preference_signal(interactions: list[Interaction]) -> dict[str, float]:
    """Sinal de preferência por livro: positivo é gosto, negativo é rejeição."""
    judged = [i for i in interactions if i.rate is not None or i.status not in UNJUDGED]
    signal = {i.book_id: UNJUDGED[i.status] for i in interactions if i not in judged}
    if judged:
        center = (sum(i.rating for i in judged) + SHRINK * NEUTRAL) / (len(judged) + SHRINK)
        signal |= {i.book_id: i.rating - center for i in judged}
    return signal


class CollaborativeModel:
    def __init__(self, book_ids: list[str], interactions: list[Interaction], k_neighbors: int = 20):
        self.book_index = {b: i for i, b in enumerate(book_ids)}
        self.k_neighbors = k_neighbors
        by_user: dict[str, list[Interaction]] = {}
        for i in interactions:
            if i.book_id in self.book_index:
                by_user.setdefault(i.user_id, []).append(i)
        self.user_ids = sorted(by_user)
        self.user_row = {u: r for r, u in enumerate(self.user_ids)}
        self.matrix = np.zeros((len(self.user_ids), len(book_ids)), dtype=np.float32)
        for row, user in enumerate(self.user_ids):
            for book, value in preference_signal(by_user[user]).items():
                self.matrix[row, self.book_index[book]] = value
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        self.normalized = self.matrix / np.where(norms == 0, 1.0, norms)

    def vector(self, signal: dict[str, float]) -> np.ndarray:
        vec = np.zeros(len(self.book_index), dtype=np.float32)
        for book, value in signal.items():
            if book in self.book_index:
                vec[self.book_index[book]] = value
        return vec

    def score(self, signal: dict[str, float], exclude_user: str | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Scores por livro e, para cada livro, quantos vizinhos o avaliaram acima da média deles."""
        n_books = len(self.book_index)
        if not len(self.user_ids):
            return np.zeros(n_books, dtype=np.float32), np.zeros(n_books, dtype=np.int64)
        vec = self.vector(signal)
        norm = np.linalg.norm(vec)
        if norm == 0:
            return np.zeros(n_books, dtype=np.float32), np.zeros(n_books, dtype=np.int64)
        sims = self.normalized @ (vec / norm)
        if exclude_user in self.user_row:
            sims[self.user_row[exclude_user]] = 0.0
        candidates = np.flatnonzero(sims > 0)
        if len(candidates) == 0:
            return np.zeros(n_books, dtype=np.float32), np.zeros(n_books, dtype=np.int64)
        top = candidates[np.argsort(-sims[candidates])[: self.k_neighbors]]
        neighbors = self.matrix[top]
        scores = sims[top] @ neighbors
        supporters = (neighbors > 0).sum(axis=0)
        return scores.astype(np.float32), supporters
