import time

import jwt

from .conftest import JWT_SECRET


def _token(sub: str, secret: str = JWT_SECRET, expires_in: int = 3600) -> dict:
    claims = {"sub": sub, "aud": "authenticated", "exp": int(time.time()) + expires_in, "role": "authenticated"}
    return {"Authorization": f"Bearer {jwt.encode(claims, secret, algorithm='HS256')}"}


def test_missing_token_is_401(auth_client):
    assert auth_client.get("/recommend/u1").status_code == 401


def test_token_of_another_user_is_403(auth_client):
    assert auth_client.get("/recommend/u1", headers=_token("u2")).status_code == 403


def test_own_token_is_200_and_uuid_case_is_ignored(auth_client):
    assert auth_client.get("/recommend/U1", headers=_token("u1")).status_code == 200


def test_invalid_or_expired_token_is_401(auth_client):
    assert auth_client.get("/recommend/u1", headers=_token("u1", secret="outro" * 8)).status_code == 401
    assert auth_client.get("/recommend/u1", headers=_token("u1", expires_in=-10)).status_code == 401


def test_user_data_routes_are_protected(auth_client):
    assert auth_client.get("/users/u1/data").status_code == 401
    assert auth_client.delete("/users/u1/data", headers=_token("u2")).status_code == 403
    assert auth_client.get("/users/u1/data", headers=_token("u1")).status_code == 200


def test_public_catalog_does_not_need_token(auth_client):
    assert auth_client.get("/books").status_code == 200
    assert auth_client.get("/trending").status_code == 200
