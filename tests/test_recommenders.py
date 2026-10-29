import numpy as np

from gana.data.source import DataState
from gana.domain import Book, Interaction, User
from gana.recommender.collaborative import preference_signal
from gana.recommender.engine import Recommender, adaptive_alpha, blend_weights

from .conftest import TODAY


def test_preference_signal_abandoned_is_negative_and_reading_positive():
    signal = preference_signal(
        [
            Interaction("u", "a", "Lido", 5.0),
            Interaction("u", "b", "Lido", 4.0),
            Interaction("u", "c", "Abandonado"),
            Interaction("u", "d", "Lendo"),
            Interaction("u", "e", "Quero ler"),
        ]
    )
    assert signal["a"] > signal["b"] > 0
    assert signal["c"] < 0
    assert signal["d"] > 0 and signal["e"] > 0


def test_single_read_is_not_zeroed_by_centering():
    assert preference_signal([Interaction("u", "a", "Lido")])["a"] > 0


def test_blend_weights_move_from_popularity_to_collaborative():
    alphas, gammas = zip(*[blend_weights(n) for n in (0, 1, 3, 5, 50)], strict=True)
    assert list(alphas) == sorted(alphas) and alphas[0] == 0 and alphas[-1] < 0.3
    assert list(gammas) == sorted(gammas, reverse=True) and gammas[0] == 0.5
    assert adaptive_alpha(5) == alphas[3] == 0.15


def test_hybrid_uses_adaptive_alpha_by_default(engine):
    result = engine.recommend("u2")  # 5 interações
    assert result.strategy == "hybrid" and result.alpha == 0.15


def test_every_recommendation_has_reasons(engine, state):
    for user_id in state.users:
        for item in engine.recommend(user_id, 5).items:
            assert item.reasons, (user_id, item.book.title)


def test_abandoned_book_pushes_away_its_category():
    books = [
        Book("t1", "Thriller 1", ["A"], "Thriller", ["Thriller"]),
        Book("t2", "Thriller 2", ["B"], "Thriller", ["Thriller"]),
        Book("s1", "Sci-fi 1", ["C"], "Science Fiction", ["Science Fiction"]),
        Book("s2", "Sci-fi 2", ["D"], "Science Fiction", ["Science Fiction"]),
        Book("r1", "Romance 1", ["E"], "Romance", ["Romance"]),
    ]
    users = {"x": User("x", personalization_consent=True)}
    interactions = [Interaction("x", "t1", "Abandonado"), Interaction("x", "s1", "Lido", 5.0)]
    engine = Recommender(DataState(users, {b.book_id: b for b in books}, interactions), today=TODAY)
    ranked = [i.book.book_id for i in engine.recommend("x", 3, algorithm="content").items]
    assert ranked[0] == "s2"
    assert ranked[-1] == "t2"  # o thriller restante vai para o fim


def test_collaborative_ignores_dissimilar_readers(engine):
    # u7 lê suspense; o colaborativo puro não deve trazer só história/biografia (gosto do u4/u8)
    titles = [i.book.main_category for i in engine.recommend("u7", 3, algorithm="collaborative").items]
    assert "Biography" not in titles[:1]


def test_scores_are_percentiles_between_zero_and_about_one(engine, state):
    scores = engine.scores(state.users["u1"], engine.signal_of("u1"))
    assert np.all(scores.final >= 0) and np.all(scores.final <= 1.06)
