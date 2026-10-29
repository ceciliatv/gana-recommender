"""Avaliação offline do motor (spec 006), substituindo o evaluator.py da POC.

Dois protocolos no Goodbooks-10k adaptado:

- leave-one-out: um livro bem avaliado (nota >= 4) de cada usuário fica escondido;
  todos os modelos treinam sem ele e o ranking é completo (sem amostrar negativos);
- cold start: 500 usuários de teste ficam com só k interações visíveis
  (k = 0, 1, 3) e informam três gêneros "de onboarding" (as categorias principais
  mais frequentes do histórico deles); o alvo são os livros bem avaliados escondidos.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np

from gana.data.source import DataState
from gana.domain import Book, Interaction, User
from gana.evaluation import goodbooks
from gana.recommender.collaborative import preference_signal
from gana.recommender.engine import Recommender

TODAY = date(2026, 1, 1)
POSITIVE = 4.0
Strategy = Callable[[Recommender, User, dict[str, float]], np.ndarray]

LOO_STRATEGIES: dict[str, Strategy] = {
    "popularidade (contagem)": lambda r, u, s: r.counts,
    "popularidade bayesiana": lambda r, u, s: r.popularity,
    "colaborativo": lambda r, u, s: r.scores(u, s, "collaborative").final,
    "conteúdo": lambda r, u, s: r.scores(u, s, "content").final,
    "híbrido α=0,3": lambda r, u, s: r.scores(u, s, "hybrid", 0.3).final,
    "híbrido α=0,5": lambda r, u, s: r.scores(u, s, "hybrid", 0.5).final,
    "híbrido α=0,7": lambda r, u, s: r.scores(u, s, "hybrid", 0.7).final,
    "híbrido adaptativo (Gana)": lambda r, u, s: r.scores(u, s).final,
}

COLD_STRATEGIES: dict[str, Strategy] = {
    "popularidade (contagem)": LOO_STRATEGIES["popularidade (contagem)"],
    "popularidade bayesiana": LOO_STRATEGIES["popularidade bayesiana"],
    "colaborativo": LOO_STRATEGIES["colaborativo"],
    "conteúdo só do histórico": lambda r, u, s: r.scores(replace(u, favorite_genres=[]), s, "content").final,
    "em camadas (Gana)": lambda r, u, s: r.scores(u, s).final,
}


def ranking_metrics(scores: np.ndarray, seen: list[int], targets: list[int], k: int = 10) -> tuple[float, float, float]:
    """HR@k, NDCG@k e Recall@2k com os itens já vistos fora do ranking."""
    scores = scores.astype(np.float64, copy=True)
    scores[seen] = -np.inf
    top = np.argsort(-scores, kind="stable")[: 2 * k]
    targets_set = set(targets)
    hits = [i in targets_set for i in top[:k]]
    discounts = 1 / np.log2(np.arange(2, k + 2))
    ideal = discounts[: min(k, len(targets))].sum()
    ndcg = float(np.dot(hits, discounts) / ideal) if ideal else 0.0
    recall = len(targets_set & set(top.tolist())) / min(2 * k, len(targets)) if targets else 0.0
    return float(any(hits)), ndcg, recall


def _evaluate(rec: Recommender, cases, strategies: dict[str, Strategy]) -> dict[str, dict[str, float]]:
    """`cases`: lista de (usuário, sinal visível, índices-alvo)."""
    results = {}
    for name, strategy in strategies.items():
        values = []
        for user, signal, targets in cases:
            if name == "colaborativo" and not signal:
                continue  # sem interações o colaborativo não tem o que dizer
            seen = [rec.index[b] for b in signal]
            values.append(ranking_metrics(strategy(rec, user, signal), seen, targets))
        if values:
            hr, ndcg, recall = np.mean(values, axis=0)
            results[name] = {"hr@10": round(hr, 4), "ndcg@10": round(ndcg, 4), "recall@20": round(recall, 4)}
    return results


def leave_one_out(books: list[Book], users: list[User], interactions: list[Interaction], seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    by_user: dict[str, list[Interaction]] = {}
    for i in interactions:
        by_user.setdefault(i.user_id, []).append(i)
    held: dict[str, Interaction] = {}
    for user_id, items in by_user.items():
        positives = [i for i in items if i.rating >= POSITIVE]
        if len(positives) >= 2:
            held[user_id] = positives[int(rng.integers(len(positives)))]
    hidden = set(held.values())
    state = DataState(
        {u.user_id: u for u in users}, {b.book_id: b for b in books}, [i for i in interactions if i not in hidden]
    )
    rec = Recommender(state, today=TODAY)
    user_map = {u.user_id: u for u in users}
    cases = []
    for user_id, target in held.items():
        signal = preference_signal([i for i in by_user[user_id] if i is not target])
        cases.append((user_map[user_id], signal, [rec.index[target.book_id]]))
    return {"users": len(cases), "results": _evaluate(rec, cases, LOO_STRATEGIES)}


def cold_start(
    books: list[Book],
    users: list[User],
    interactions: list[Interaction],
    ks: tuple[int, ...] = (0, 1, 3),
    n_test: int = 500,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    book_map = {b.book_id: b for b in books}
    by_user: dict[str, list[Interaction]] = {}
    for i in interactions:
        by_user.setdefault(i.user_id, []).append(i)
    eligible = sorted(u for u, items in by_user.items() if sum(i.rating >= POSITIVE for i in items) >= 8)
    test_ids = set(rng.choice(eligible, size=min(n_test, len(eligible)), replace=False).tolist())
    shuffled = {u: [by_user[u][j] for j in rng.permutation(len(by_user[u]))] for u in test_ids}
    genres = {}
    for u in test_ids:
        counts = Counter(book_map[i.book_id].main_category for i in by_user[u] if book_map[i.book_id].main_category)
        genres[u] = [g for g, _ in counts.most_common(3)]

    report = {"test_users": len(test_ids), "by_k": {}}
    for k in ks:
        visible = {u: shuffled[u][:k] for u in test_ids}
        train = [i for i in interactions if i.user_id not in test_ids] + [i for u in test_ids for i in visible[u]]
        test_users = {u.user_id: replace(u, favorite_genres=genres.get(u.user_id, [])) for u in users}
        rec = Recommender(DataState(test_users, book_map, train), today=TODAY)
        cases = []
        for u in sorted(test_ids):
            shown = {i.book_id for i in visible[u]}
            targets = [rec.index[i.book_id] for i in shuffled[u][k:] if i.rating >= POSITIVE and i.book_id not in shown]
            cases.append((test_users[u], preference_signal(visible[u]), targets))
        report["by_k"][str(k)] = _evaluate(rec, cases, COLD_STRATEGIES)
    return report


def render(report: dict) -> str:
    lines = [
        "# Avaliação offline do motor do Gana",
        "",
        f"Goodbooks-10k adaptado ao esquema do Gana: {report['users']} usuários amostrados (semente 42), "
        f"{report['books']} livros, {report['interactions']} interações. Ranking completo, sem amostrar negativos.",
        "",
        f"## Leave-one-out ({report['loo']['users']} usuários)",
        "",
        "| Estratégia | HR@10 | NDCG@10 |",
        "|---|---:|---:|",
    ]
    best = max(v["ndcg@10"] for v in report["loo"]["results"].values())
    for name, m in report["loo"]["results"].items():
        mark = "**" if m["ndcg@10"] == best else ""
        lines.append(f"| {name} | {m['hr@10']:.4f} | {mark}{m['ndcg@10']:.4f}{mark} |")
    cold = report["cold_start"]
    lines += [
        "",
        f"## Cold start ({cold['test_users']} usuários de teste)",
        "",
        "Recall@20 com só k interações visíveis e três gêneros de onboarding.",
        "",
        "| Estratégia | " + " | ".join(f"k={k}" for k in cold["by_k"]) + " |",
        "|---|" + "---:|" * len(cold["by_k"]),
    ]
    names = list(next(iter(cold["by_k"].values())).keys())
    for name in COLD_STRATEGIES:
        if name not in names and not any(name in v for v in cold["by_k"].values()):
            continue
        cells = [f"{v[name]['recall@20']:.4f}" if name in v else "—" for v in cold["by_k"].values()]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def run(data_dir: Path, out_dir: Path, n_users: int = 3000, log=print) -> dict:
    books, users, interactions = goodbooks.load(data_dir / "goodbooks", n_users=n_users, log=log)
    log(f"{len(users)} usuários, {len(books)} livros, {len(interactions)} interações")
    log("leave-one-out...")
    loo = leave_one_out(books, users, interactions)
    log("cold start...")
    cold = cold_start(books, users, interactions)
    report = {
        "users": len(users),
        "books": len(books),
        "interactions": len(interactions),
        "loo": loo,
        "cold_start": cold,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "offline.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (out_dir / "offline.md").write_text(render(report))
    log(render(report))
    return report
