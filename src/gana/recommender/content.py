"""Filtragem baseada em conteúdo: TF-IDF sobre categoria principal, categorias e autores.

A categoria principal entra com peso 2 (sinal mais forte de preferência, como na
POC). O perfil da pessoa é a soma dos vetores dos livros ponderada pelo rating
centrado: livros abandonados afastam o perfil do que eles têm.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.preprocessing import normalize

from gana.domain import Book


def _features(book: Book) -> dict[str, float]:
    feats: dict[str, float] = {}
    if book.main_category:
        feats[f"cat:{book.main_category.lower()}"] = 2.0
    for category in book.categories:
        key = f"cat:{category.lower()}"
        feats[key] = max(feats.get(key, 0.0), 1.0)
    for author in book.author:
        feats[f"author:{author.strip().lower()}"] = 1.0
    return feats


class ContentModel:
    def __init__(self, books: list[Book]):
        self.books = books
        self.vectorizer = DictVectorizer()
        counts = self.vectorizer.fit_transform([_features(b) for b in books])
        self.tfidf = TfidfTransformer(sublinear_tf=False)
        self.matrix = normalize(self.tfidf.fit_transform(counts)).tocsr()
        self.vocabulary = self.vectorizer.vocabulary_

    def genre_vector(self, genres: list[str]) -> sparse.csr_matrix:
        vec = sparse.lil_matrix((1, self.matrix.shape[1]), dtype=np.float64)
        for genre in genres:
            col = self.vocabulary.get(f"cat:{genre.lower()}")
            if col is not None:
                vec[0, col] = self.tfidf.idf_[col]
        return vec.tocsr()

    def profile(
        self, weights: dict[int, float], genres: list[str] | None = None, genre_weight: float = 1.0
    ) -> sparse.csr_matrix:
        """`weights`: índice do livro -> sinal de preferência. `genres`: do onboarding.

        Os gêneros entram como um vetor unitário com o peso de um livro curtido, para
        não apagar o histórico de quem já leu alguma coisa.
        """
        vec = sparse.csr_matrix((1, self.matrix.shape[1]))
        if weights:
            rows = np.fromiter(weights.keys(), dtype=np.int64)
            values = np.fromiter(weights.values(), dtype=np.float64)
            selector = sparse.csr_matrix((values, (np.zeros(len(rows)), rows)), shape=(1, self.matrix.shape[0]))
            vec = selector @ self.matrix
        if genres:
            vec = vec + genre_weight * normalize(self.genre_vector(genres))
        return normalize(vec)

    def score(self, profile: sparse.csr_matrix) -> np.ndarray:
        return np.asarray((self.matrix @ profile.T).todense()).ravel()

    def similarity_to(self, index: int) -> np.ndarray:
        return np.asarray((self.matrix @ self.matrix[index].T).todense()).ravel()
