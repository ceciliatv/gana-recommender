"""Goodbooks-10k (CC BY-SA 4.0) adaptado ao esquema do Gana, para a avaliação offline.

- livros: tags de prateleira do Goodreads viram `categories` (as mais fortes, sem
  tags de posse ou de leitura) e a primeira vira `main_category`;
- notas viram estante: 1 estrela → "Abandonado"; 2 a 5 → "Lido" com a nota como review.
Os dados são baixados para `data/` e não vão para o Git.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

from gana.domain import Book, Interaction, User

BASE = "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master"
FILES = ("books.csv", "ratings.csv", "book_tags.csv", "tags.csv")

_SHELF = re.compile(
    r"read|own|kindle|ebook|e-book|audio|library|favou?rite|fav|wish|buy|default|shelf|series|book|novel"
    r"|dnf|tbr|\d|my-|i-|have|bought|borrow|giveaway|kobo|nook|calibre|wanted|stars?|^to-"
)
_ALIASES = {
    "sci-fi": "Science Fiction",
    "science-fiction": "Science Fiction",
    "scifi": "Science Fiction",
    "ya": "Young Adult",
    "young-adult": "Young Adult",
    "non-fiction": "Non-Fiction",
    "nonfiction": "Non-Fiction",
    "historical-fiction": "Historical Fiction",
    "chick-lit": "Chick Lit",
}
_SKIP = {"fiction", "adult", "adult-fiction", "general-fiction", "literature", "classic-literature"}


def download(folder: Path, log=print) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = folder / name
        if dest.exists() and dest.stat().st_size:
            continue
        log(f"baixando {name}")
        with httpx.stream("GET", f"{BASE}/{name}", follow_redirects=True, timeout=120) as response:
            response.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in response.iter_bytes(1 << 20):
                    fh.write(chunk)
    return folder


def clean_tag(raw: str) -> str | None:
    tag = str(raw).strip().lower()
    if tag in _ALIASES:
        return _ALIASES[tag]
    if len(tag) < 3 or tag in _SKIP or _SHELF.search(tag):
        return None
    return tag.replace("-", " ").title()


def books_from_frames(books: pd.DataFrame, book_tags: pd.DataFrame, tags: pd.DataFrame, top: int = 6) -> list[Book]:
    names = tags.set_index("tag_id")["tag_name"]
    tagged = book_tags.assign(name=book_tags["tag_id"].map(names)).sort_values("count", ascending=False)
    by_book: dict[int, list[str]] = {}
    for gr_id, group in tagged.groupby("goodreads_book_id", sort=False):
        cleaned: list[str] = []
        for name in group["name"]:
            tag = clean_tag(name)
            if tag and tag not in cleaned:
                cleaned.append(tag)
            if len(cleaned) == top:
                break
        by_book[int(gr_id)] = cleaned
    result = []
    for row in books.itertuples(index=False):
        categories = by_book.get(int(row.goodreads_book_id), [])
        year = row.original_publication_year
        result.append(
            Book(
                google_books_id=f"gb-{row.book_id}",
                title=re.sub(r"\s*\([^)]*\)", "", str(row.title)).strip(),
                author=[a.strip() for a in str(row.authors).split(",") if a.strip()][:3],
                main_category=categories[0] if categories else "",
                categories=categories,
                year_published=int(year) if pd.notna(year) else 0,
            )
        )
    return result


def interactions_from_ratings(ratings: pd.DataFrame) -> list[Interaction]:
    out = []
    for user, book, rating in ratings[["user_id", "book_id", "rating"]].itertuples(index=False):
        if rating <= 1:
            out.append(Interaction(f"user-{user}", f"gb-{book}", "Abandonado"))
        else:
            out.append(Interaction(f"user-{user}", f"gb-{book}", "Lido", float(rating)))
    return out


def load(folder: Path, n_users: int = 3000, min_ratings: int = 10, seed: int = 42, log=print):
    download(folder, log)
    books = pd.read_csv(folder / "books.csv")
    ratings = pd.read_csv(folder / "ratings.csv")
    counts = ratings["user_id"].value_counts()
    eligible = np.sort(counts[counts >= min_ratings].index.to_numpy())
    chosen = np.random.default_rng(seed).choice(eligible, size=min(n_users, len(eligible)), replace=False)
    ratings = ratings[ratings["user_id"].isin(chosen)]
    catalog = books_from_frames(books, pd.read_csv(folder / "book_tags.csv"), pd.read_csv(folder / "tags.csv"))
    users = [User(f"user-{u}", date(1990, 1, 1), personalization_consent=True) for u in chosen]
    return catalog, users, interactions_from_ratings(ratings)
