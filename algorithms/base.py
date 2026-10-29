from abc import ABC, abstractmethod
from typing import List


class BaseRecommender(ABC):
    """Interface comum para todos os algoritmos de recomendação."""

    def __init__(self, users: list, books: list, interactions: list):
        self.users = users
        self.books = books
        self.interactions = interactions
        self.book_map = {b["book_id"]: b for b in books}
        self.user_map = {u["user_id"]: u for u in users}

    @abstractmethod
    def fit(self):
        """Treina/prepara o modelo com os dados disponíveis."""

    @abstractmethod
    def recommend(self, user_id: str, n: int = 5) -> List[dict]:
        """
        Retorna lista de n livros recomendados para o usuário.
        Cada item: {"book_id", "title", "main_category", "score"}
        """

    def _already_read(self, user_id: str) -> set:
        return {book_id for uid, book_id, _ in self.interactions if uid == user_id}

    def _format(self, book_id: str, score: float) -> dict:
        b = self.book_map[book_id]
        return {
            "book_id": book_id,
            "title": b["title"],
            "main_category": b["main_category"],
            "score": round(score, 4),
        }
