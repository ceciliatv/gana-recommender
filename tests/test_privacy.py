from dataclasses import replace
from datetime import date

from gana.data.source import DataState
from gana.domain import User
from gana.privacy import age_band, age_on, content_allowed, is_sensitive, may_personalize, pseudonymize
from gana.recommender.engine import Recommender

from .conftest import TODAY

MATURE_ID = "mock-50tons"


def test_age_on_counts_birthday():
    assert age_on(date(2008, 10, 30), date(2026, 10, 29)) == 17
    assert age_on(date(2008, 10, 29), date(2026, 10, 29)) == 18
    assert age_on(None) is None


def test_age_bands():
    assert age_band(User("a", date(2017, 1, 1)), TODAY) == "crianca"
    assert age_band(User("a", date(2011, 1, 1)), TODAY) == "adolescente"
    assert age_band(User("a", date(1990, 1, 1)), TODAY) == "adulto"
    assert age_band(User("a"), TODAY) == "desconhecida"


def test_personalization_requires_consent_and_parental_consent_for_children():
    assert not may_personalize(User("a", date(1990, 1, 1), personalization_consent=False), TODAY)
    assert not may_personalize(User("a", date(2017, 1, 1), personalization_consent=True), TODAY)
    assert may_personalize(User("a", date(2017, 1, 1), True, parental_consent=True), TODAY)
    assert may_personalize(User("a", None, personalization_consent=True), TODAY)


def test_sensitive_books(state):
    assert is_sensitive(state.books[MATURE_ID])
    assert not content_allowed(state.books[MATURE_ID], User("a"), TODAY)  # idade desconhecida
    assert content_allowed(state.books[MATURE_ID], User("a", date(1990, 1, 1)), TODAY)


def test_minors_and_unknown_age_never_get_mature_books(engine, state):
    state.users["sem-idade"] = User("sem-idade", None, True, False, ["Romance"])
    engine = Recommender(state, today=TODAY)
    for user_id in ("u10-teen", "u11-crianca", "sem-idade"):
        ids = [i.book.book_id for i in engine.recommend(user_id, 18).items]
        assert MATURE_ID not in ids, user_id
    assert MATURE_ID not in [t.book.book_id for t in engine.trending(18)]
    assert MATURE_ID not in [s.book.book_id for s in engine.similar("vNxMMQEACAAJ", 18)]


def test_adults_can_get_mature_books(engine, state):
    state.users["adulta"] = User("adulta", date(1990, 1, 1), True, False, ["Romance"])
    ids = [i.book.book_id for i in Recommender(state, today=TODAY).recommend("adulta", 18).items]
    assert MATURE_ID in ids


def test_without_consent_is_non_personalized(engine):
    assert engine.recommend("u12-sem-consentimento").strategy == "non_personalized"
    assert engine.recommend("u11-crianca").strategy == "non_personalized"


def test_non_consenting_reads_do_not_influence_anyone(state):
    with_them = Recommender(state, today=TODAY)
    without = DataState(
        state.users, state.books, [i for i in state.interactions if i.user_id != "u12-sem-consentimento"]
    )
    without_them = Recommender(without, today=TODAY)
    for user_id in ("u2", "u7", "u3"):
        a = [(i.book.book_id, i.score) for i in with_them.recommend(user_id, 10).items]
        b = [(i.book.book_id, i.score) for i in without_them.recommend(user_id, 10).items]
        assert a == b, user_id


def test_consent_withdrawal_removes_reads_from_training(state):
    state.users["u7"] = replace(state.users["u7"], personalization_consent=False)
    engine = Recommender(state, today=TODAY)
    assert all(i.user_id != "u7" for i in engine.training)


def test_pseudonymize_is_stable_and_hides_id():
    assert pseudonymize("u1", "sal") == pseudonymize("u1", "sal")
    assert pseudonymize("u1", "sal") != pseudonymize("u1", "outro-sal")
    assert "u1" not in pseudonymize("u1", "sal")


def test_user_data_access_and_deletion(client):
    data = client.get("/users/U10-TEEN/data").json()
    assert data["age_band"] == "adolescente"
    assert data["interactions"] == [{"book_id": "vNxMMQEACAAJ", "status": "Lido", "rate": 5.0}]
    assert "name" not in data and "username" not in data
    assert client.delete("/users/u10-teen/data").status_code == 200
    assert client.get("/users/u10-teen/data").status_code == 404
    assert client.get("/recommend/u10-teen").status_code == 404
