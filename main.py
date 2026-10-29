"""
Ponto de entrada da POC.
Treina os três algoritmos, mostra recomendações para um usuário de exemplo
e compara as métricas de todos.
"""

from data.source import build_source
from algorithms.collaborative import CollaborativeRecommender
from algorithms.content_based import ContentBasedRecommender
from algorithms.hybrid import HybridRecommender
from evaluator import evaluate

SEPARATOR = "-" * 55


def print_recs(label: str, recs: list):
    print(f"\n  [{label}]")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r['title']} ({r['main_category']})  score={r['score']}")


def main():
    source, label = build_source()
    print(f"Fonte de dados: {label}")
    users = source.get_users()
    books = source.get_books()
    interactions = list(source.get_interactions())

    # --- treina modelos completos ---
    collab  = CollaborativeRecommender(users, books, interactions)
    content = ContentBasedRecommender(users, books, interactions)
    hybrid  = HybridRecommender(users, books, interactions, alpha=0.5)

    collab.fit()
    content.fit()
    hybrid.fit()

    # --- demonstração: recomendações para cada usuário ---
    print(f"\n{'='*55}")
    print(" RECOMENDAÇÕES POR USUÁRIO")
    print(f"{'='*55}")

    for user in users:
        uid  = user["user_id"]
        name = user["name"]
        print(f"\n{SEPARATOR}")
        print(f" Usuário: {name} (@{user['username']})")
        print_recs("Collaborative", collab.recommend(uid, 3))
        print_recs("Content-Based", content.recommend(uid, 3))
        print_recs("Hybrid (α=0.5)", hybrid.recommend(uid, 3))

    # --- avaliação comparativa ---
    print(f"\n\n{'='*55}")
    print(" AVALIAÇÃO DOS ALGORITMOS (leave-one-out, top-5)")
    print(f"{'='*55}")
    print(f"{'Algoritmo':<22} {'Precision':>9} {'Recall':>9} {'HitRate':>9} {'Users':>6}")
    print(SEPARATOR)

    configs = [
        ("Collaborative",     CollaborativeRecommender, {}),
        ("Content-Based",     ContentBasedRecommender,  {}),
        ("Hybrid α=0.3",      HybridRecommender,        {"alpha": 0.3}),
        ("Hybrid α=0.5",      HybridRecommender,        {"alpha": 0.5}),
        ("Hybrid α=0.7",      HybridRecommender,        {"alpha": 0.7}),
    ]

    for name, cls, kwargs in configs:
        m = evaluate(cls, users, books, interactions, n=5, cls_kwargs=kwargs)
        print(f"{name:<22} {m['precision']:>9.4f} {m['recall']:>9.4f} {m['hit_rate']:>9.4f} {m['evaluated_users']:>6}")

    print(SEPARATOR)


if __name__ == "__main__":
    main()
