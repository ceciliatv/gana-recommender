from datetime import date

import pytest
from fastapi.testclient import TestClient

from gana.api.app import create_app
from gana.config import Settings
from gana.data.source import DataState, MockSource
from gana.recommender.engine import Recommender

TODAY = date(2026, 10, 29)
JWT_SECRET = "segredo-de-teste-com-mais-de-32-bytes!!"


def settings(jwt_secret: str | None = None) -> Settings:
    return Settings(None, None, jwt_secret, None, "sal-de-teste")


@pytest.fixture
def state() -> DataState:
    return DataState.load(MockSource())


@pytest.fixture
def engine(state) -> Recommender:
    return Recommender(state, today=TODAY)


@pytest.fixture
def client():
    with TestClient(create_app(settings(), MockSource())) as c:
        yield c


@pytest.fixture
def auth_client():
    with TestClient(create_app(settings(JWT_SECRET), MockSource())) as c:
        yield c
