"""O app iOS decodifica estes campos (Data/DTOs/RecommendationDTO.swift no repositório do app)."""

RECOMMENDATION_DTO = {"user_id", "algorithm", "recommendations"}
RECOMMENDATION_ITEM_DTO = {"book_id", "title", "main_category", "categories", "author", "url_image", "score"}
BOOK_DTO = {
    "book_id",
    "google_books_id",
    "title",
    "author",
    "main_category",
    "categories",
    "pages",
    "year_published",
    "url_image",
}


def test_recommend_keeps_ios_contract(client):
    body = client.get("/recommend/u1", params={"algorithm": "hybrid", "n": 3}).json()
    assert body.keys() >= RECOMMENDATION_DTO
    assert len(body["recommendations"]) == 3
    for item in body["recommendations"]:
        assert item.keys() >= RECOMMENDATION_ITEM_DTO
        assert item["reasons"]


def test_uppercase_uuid_from_ios_is_normalized(client):
    assert client.get("/recommend/U1").status_code == 200


def test_books_trending_similar_keep_book_dto(client):
    for path in ("/books", "/trending", "/similar/ydQiAQAAIAAJ"):
        rows = client.get(path).json()
        assert rows, path
        assert all(row.keys() >= BOOK_DTO for row in rows)


def test_similar_unknown_book_returns_empty_list(client):
    assert client.get("/similar/nao-existe").json() == []


def test_unknown_user_is_404(client):
    assert client.get("/recommend/ninguem").status_code == 404


def test_algorithms_and_fixed_alpha(client):
    for algorithm in ("collaborative", "content", "hybrid"):
        assert client.get("/recommend/u2", params={"algorithm": algorithm}).json()["algorithm"] == algorithm
    assert client.get("/recommend/u2", params={"alpha": 0.9}).json()["alpha"] == 0.9


def test_users_listing_was_removed(client):
    assert client.get("/users").status_code == 404


def test_interaction_updates_recommendations(client):
    before = [r["book_id"] for r in client.get("/recommend/u4", params={"n": 10}).json()["recommendations"]]
    target = before[0]
    response = client.post("/interactions", json={"user_id": "U4", "book_id": target, "status": "Lido", "rate": 5})
    assert response.status_code == 201 and response.json()["effective_rating"] == 5
    after = [r["book_id"] for r in client.get("/recommend/u4", params={"n": 10}).json()["recommendations"]]
    assert target not in after


def test_health_and_refresh(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.post("/refresh").json()["books"] == 18
