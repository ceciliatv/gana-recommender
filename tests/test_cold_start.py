from dataclasses import replace

from gana.domain import Interaction
from gana.recommender.engine import Recommender

from .conftest import TODAY


def test_new_user_with_onboarding_genres(engine):
    result = engine.recommend("u9-novo", 4)
    assert result.strategy == "cold_start_genres"
    assert all(i.book.main_category in {"Science Fiction", "Fantasy"} for i in result.items)
    assert all("gênero" in i.reasons[0] for i in result.items)


def test_genres_parameter_overrides_profile(engine):
    result = engine.recommend("u9-novo", 3, genres=["History"])
    assert all(i.book.main_category == "History" for i in result.items[:2])


def test_new_user_without_genres_gets_popularity(state):
    state.users["u9-novo"] = replace(state.users["u9-novo"], favorite_genres=[])
    result = Recommender(state, today=TODAY).recommend("u9-novo", 3)
    assert result.strategy == "popularity"
    trending = [b.book.book_id for b in Recommender(state, today=TODAY).trending(3, state.users["u9-novo"])]
    assert [i.book.book_id for i in result.items] == trending


def test_book_without_interactions_can_be_recommended(engine):
    # Projeto Hail Mary não tem interações de quem consentiu: só pode vir pelo conteúdo.
    # O prior de popularidade o empurra para baixo, mas não o tira da lista de quem lê ficção científica.
    assert "Projeto Hail Mary" in [i.book.title for i in engine.recommend("u6", 3).items]
    assert "Projeto Hail Mary" in [i.book.title for i in engine.recommend("u2", 5).items]


def test_few_interactions_blend_onboarding_genres(state):
    state.interactions.append(Interaction("u9-novo", "vNxMMQEACAAJ", "Lido", 5.0))  # um romance
    result = Recommender(state, today=TODAY).recommend("u9-novo", 5)
    assert result.strategy == "hybrid"
    assert {i.book.main_category for i in result.items} & {"Science Fiction", "Fantasy"}


def test_trending_uses_bayesian_popularity(engine):
    trending = engine.trending(18)
    assert all(t.book.title != "Projeto Hail Mary" for t in trending)  # sem leitores que consentiram
    scores = [t.score for t in trending]
    assert scores == sorted(scores, reverse=True)
