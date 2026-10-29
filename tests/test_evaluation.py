import numpy as np
import pandas as pd
import pytest

from gana.evaluation.goodbooks import books_from_frames, clean_tag, interactions_from_ratings
from gana.evaluation.offline import ranking_metrics


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("sci-fi", "Science Fiction"),
        ("to-read", None),
        ("favorites", None),
        ("fantasy", "Fantasy"),
        ("2015-reads", None),
        ("fiction", None),
        ("historical-fiction", "Historical Fiction"),
    ],
)
def test_clean_tag(raw, expected):
    assert clean_tag(raw) == expected


def test_books_from_frames_builds_categories():
    books = pd.DataFrame(
        [
            {
                "book_id": 1,
                "goodreads_book_id": 10,
                "title": "Dune (Dune Chronicles, #1)",
                "authors": "Frank Herbert",
                "original_publication_year": 1965.0,
            }
        ]
    )
    book_tags = pd.DataFrame({"goodreads_book_id": [10, 10, 10], "tag_id": [1, 2, 3], "count": [900, 500, 100]})
    tags = pd.DataFrame({"tag_id": [1, 2, 3], "tag_name": ["to-read", "sci-fi", "space-opera"]})
    [book] = books_from_frames(books, book_tags, tags)
    assert book.title == "Dune" and book.google_books_id == "gb-1"
    assert book.main_category == "Science Fiction" and book.categories == ["Science Fiction", "Space Opera"]


def test_ratings_become_shelf_statuses():
    ratings = pd.DataFrame({"user_id": [1, 1], "book_id": [5, 6], "rating": [1, 4]})
    abandoned, read = interactions_from_ratings(ratings)
    assert abandoned.status == "Abandonado" and abandoned.rate is None
    assert read.status == "Lido" and read.rate == 4.0


def test_ranking_metrics_hand_computed():
    scores = np.array([0.9, 0.8, 0.7, 0.1])
    # item 0 já visto; alvo 2 fica em 2º lugar -> NDCG = 1/log2(3)
    hr, ndcg, recall = ranking_metrics(scores, seen=[0], targets=[2], k=2)
    assert hr == 1.0 and ndcg == pytest.approx(1 / np.log2(3)) and recall == 1.0
    hr, ndcg, _ = ranking_metrics(scores, seen=[], targets=[3], k=2)
    assert hr == 0.0 and ndcg == 0.0
