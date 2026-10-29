"""Popularidade bayesiana (spec 003).

score = log(1 + v) · (v·R + m·C) / (v + m)
  v = interações do livro, R = rating médio do livro,
  C = rating médio global, m = mediana de interações por livro.

A média bayesiana sozinha mede qualidade e, com pouca evidência, deixa um livro
com três notas 5 na frente de um lido por centenas de pessoas: na avaliação
offline ela ficou quase em zero. Multiplicar pelo volume (em log) junta as duas
coisas, e foi melhor que a contagem pura (ver docs/specs/003).
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from gana.domain import Interaction


def interaction_counts(book_ids: list[str], interactions: list[Interaction]) -> np.ndarray:
    index = {b: i for i, b in enumerate(book_ids)}
    counts = np.zeros(len(book_ids), dtype=np.float64)
    for i in interactions:
        if i.book_id in index:
            counts[index[i.book_id]] += 1
    return counts


def bayesian_popularity(book_ids: list[str], interactions: list[Interaction]) -> np.ndarray:
    ratings: dict[str, list[float]] = defaultdict(list)
    for i in interactions:
        ratings[i.book_id].append(i.rating)
    if not ratings:
        return np.zeros(len(book_ids))
    global_mean = float(np.mean([r for rs in ratings.values() for r in rs]))
    m = float(np.median([len(rs) for rs in ratings.values()]))
    scores = np.empty(len(book_ids))
    for idx, book in enumerate(book_ids):
        rs = ratings.get(book, [])
        v = len(rs)
        mean = float(np.mean(rs)) if rs else global_mean
        scores[idx] = np.log1p(v) * (v * mean + m * global_mean) / (v + m)
    return scores
