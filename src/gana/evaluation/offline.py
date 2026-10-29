"""
Avaliação dos algoritmos usando leave-one-out:
remove a última interação de cada usuário, treina sem ela, e verifica
se o item removido aparece nas top-N recomendações.

Métricas:
  - Precision@N : dos N recomendados, quantos são relevantes?
  - Recall@N   : dos relevantes, quantos foram recomendados?
  - Hit Rate   : porcentagem de usuários que tiveram ao menos 1 acerto no top-N
"""

from typing import Type
from algorithms.base import BaseRecommender


def evaluate(recommender_cls: Type[BaseRecommender], users, books, interactions,
             n: int = 5, cls_kwargs: dict = None) -> dict:

    cls_kwargs = cls_kwargs or {}
    hit_count = 0
    precision_list = []
    recall_list = []
    evaluated_users = 0

    # agrupa interações por usuário, ordena por posição (simula ordem temporal)
    from collections import defaultdict
    user_interactions = defaultdict(list)
    for uid, bid, rating in interactions:
        user_interactions[uid].append((bid, rating))

    for user in users:
        uid = user["user_id"]
        user_items = user_interactions[uid]

        if len(user_items) < 2:
            continue  # precisa de ao menos 2 interações para deixar uma de fora

        # deixa o último item como ground truth
        test_item = user_items[-1][0]
        train_interactions = [(uid, bid, r) for (bid, r) in user_items[:-1]]

        # mantém interações dos outros usuários intactas
        other_interactions = [(u, b, r) for (u, b, r) in interactions if u != uid]
        train_set = other_interactions + train_interactions

        model = recommender_cls(users, books, train_set, **cls_kwargs)
        model.fit()
        recs = model.recommend(uid, n)
        rec_ids = {r["book_id"] for r in recs}

        hit = test_item in rec_ids
        hit_count += int(hit)
        precision_list.append(int(hit) / n)
        recall_list.append(int(hit) / 1)  # só 1 item relevante no ground truth
        evaluated_users += 1

    if evaluated_users == 0:
        return {"precision": 0, "recall": 0, "hit_rate": 0, "evaluated_users": 0}

    return {
        "precision": round(sum(precision_list) / evaluated_users, 4),
        "recall":    round(sum(recall_list) / evaluated_users, 4),
        "hit_rate":  round(hit_count / evaluated_users, 4),
        "evaluated_users": evaluated_users,
    }
