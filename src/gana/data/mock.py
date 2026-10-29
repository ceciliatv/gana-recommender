"""Dados sintéticos no formato do banco do Gana, para rodar sem Supabase.

Os usuários são fictícios. Além dos leitores da POC (u1 a u8), há perfis para os
casos das specs 003 e 005: pessoa nova com gêneros do onboarding, adolescente,
criança sem consentimento dos responsáveis e pessoa que não consentiu com a
personalização. Os três últimos livros não têm interações (cold start de item).
"""

from __future__ import annotations

from datetime import date

from gana.domain import Book, Interaction, User


def _book(gid, title, author, main, categories, pages, year, maturity="NOT_MATURE") -> Book:
    return Book(
        google_books_id=gid,
        title=title,
        author=author,
        main_category=main,
        categories=categories,
        pages=pages,
        year_published=year,
        url_image=f"https://books.google.com/books/content?id={gid}&printsec=frontcover&img=1&zoom=1",
        maturity_rating=maturity,
    )


BOOKS: list[Book] = [
    _book("gcfGnQEACAAJ", "O Nome do Vento", ["Patrick Rothfuss"], "Fantasy", ["Fantasy", "Epic Fantasy"], 662, 2007),
    _book("ydQiAQAAIAAJ", "Duna", ["Frank Herbert"], "Science Fiction", ["Science Fiction", "Classic Sci-Fi"], 412, 1965),
    _book("vNxMMQEACAAJ", "Orgulho e Preconceito", ["Jane Austen"], "Romance", ["Romance", "Classic Literature"], 432, 1813),
    _book("AoRbAAAAMAAJ", "O Código Da Vinci", ["Dan Brown"], "Thriller", ["Thriller", "Mystery"], 454, 2003),
    _book("1EiJAwAAQBAJ", "Sapiens", ["Yuval Noah Harari"], "History", ["History", "Non-Fiction", "Anthropology"], 443, 2011),
    _book("pD6arNyKyi8C", "O Hobbit", ["J.R.R. Tolkien"], "Fantasy", ["Fantasy", "Adventure"], 310, 1937),
    _book("B4YGAQAAIAAJ", "Fundação", ["Isaac Asimov"], "Science Fiction", ["Science Fiction", "Classic Sci-Fi"], 244, 1951),
    _book("HMeNEAAAQBAJ", "A Garota no Trem", ["Paula Hawkins"], "Thriller", ["Thriller", "Mystery"], 336, 2015),
    _book("yO9EAQAAMAAJ", "Sherlock Holmes", ["Arthur Conan Doyle"], "Mystery", ["Mystery", "Classic Literature"], 307, 1892),
    _book("8U2oAAAAQBAJ", "Steve Jobs", ["Walter Isaacson"], "Biography", ["Biography", "Non-Fiction", "Technology"], 656, 2011),
    _book("FmOcAQAAQBAJ", "A Guerra dos Tronos", ["George R.R. Martin"], "Fantasy", ["Fantasy", "Epic Fantasy"], 694, 1996),
    _book("kotPYEqx7kMC", "1984", ["George Orwell"], "Science Fiction", ["Science Fiction", "Dystopia"], 328, 1949),
    _book("ExkMAAAAYAAJ", "O Morro dos Ventos Uivantes", ["Emily Brontë"], "Romance", ["Romance", "Gothic Fiction"], 342, 1847),
    _book("3J_NAAAAQBAJ", "Inferno", ["Dan Brown"], "Thriller", ["Thriller", "Mystery"], 480, 2013),
    _book("FmyBCwAAQBAJ", "Homo Deus", ["Yuval Noah Harari"], "History", ["History", "Non-Fiction", "Futurism"], 450, 2015),
    # sem interações de quem consentiu: entram só pelo conteúdo (cold start de item)
    _book("lL2GDwAAQBAJ", "Torto Arado", ["Itamar Vieira Junior"], "Fiction", ["Fiction", "Brazilian Literature"], 237, 2019),
    _book("mock-hailmary", "Projeto Hail Mary", ["Andy Weir"], "Science Fiction", ["Science Fiction", "Space"], 496, 2021),
    _book("mock-50tons", "Cinquenta Tons de Cinza", ["E L James"], "Romance", ["Romance", "Erotica"], 480, 2011, "MATURE"),
]

USERS: list[User] = [
    User("u1", date(1998, 3, 2), True, False, ["Fantasy"]),
    User("u2", date(1990, 7, 15), True),
    User("u3", date(2001, 1, 20), True),
    User("u4", date(1985, 11, 5), True),
    User("u5", date(1999, 9, 9), True),
    User("u6", date(1994, 4, 30), True),
    User("u7", date(1996, 12, 12), True),
    User("u8", date(1979, 6, 1), True),
    User("u9-novo", date(2000, 2, 2), True, False, ["Science Fiction", "Fantasy"]),  # recém-chegada
    User("u10-teen", date(2011, 5, 5), True, False, ["Romance"]),  # 15 anos
    User("u11-crianca", date(2017, 8, 8), True, False, ["Fantasy"]),  # 9 anos, sem consentimento dos pais
    User("u12-sem-consentimento", date(1992, 10, 10), False),
]

# (usuário, livro, status, nota da review ou None)
_SHELF = [
    ("u1", "gcfGnQEACAAJ", "Lido", 5.0),
    ("u1", "pD6arNyKyi8C", "Lido", 4.0),
    ("u1", "FmOcAQAAQBAJ", "Lido", 5.0),
    ("u1", "vNxMMQEACAAJ", "Lido", 4.0),
    ("u1", "ExkMAAAAYAAJ", "Lendo", None),
    ("u2", "ydQiAQAAIAAJ", "Lido", 5.0),
    ("u2", "B4YGAQAAIAAJ", "Lido", 5.0),
    ("u2", "kotPYEqx7kMC", "Lido", 4.0),
    ("u2", "AoRbAAAAMAAJ", "Lido", 4.0),
    ("u2", "HMeNEAAAQBAJ", "Abandonado", None),
    ("u3", "gcfGnQEACAAJ", "Lido", 4.0),
    ("u3", "pD6arNyKyi8C", "Lido", 5.0),
    ("u3", "yO9EAQAAMAAJ", "Lido", 5.0),
    ("u3", "FmOcAQAAQBAJ", "Lendo", None),
    ("u4", "1EiJAwAAQBAJ", "Lido", 5.0),
    ("u4", "8U2oAAAAQBAJ", "Lido", 4.0),
    ("u4", "FmyBCwAAQBAJ", "Lido", 5.0),
    ("u5", "gcfGnQEACAAJ", "Lido", 5.0),
    ("u5", "vNxMMQEACAAJ", "Lido", 5.0),
    ("u5", "pD6arNyKyi8C", "Lido", 4.0),
    ("u5", "FmOcAQAAQBAJ", "Lido", 4.0),
    ("u5", "ExkMAAAAYAAJ", "Lido", 5.0),
    ("u6", "ydQiAQAAIAAJ", "Lido", 4.0),
    ("u6", "B4YGAQAAIAAJ", "Lido", None),
    ("u6", "1EiJAwAAQBAJ", "Lido", 5.0),
    ("u6", "kotPYEqx7kMC", "Lido", 5.0),
    ("u6", "FmyBCwAAQBAJ", "Lendo", None),
    ("u7", "yO9EAQAAMAAJ", "Lido", 5.0),
    ("u7", "AoRbAAAAMAAJ", "Lido", 4.0),
    ("u7", "HMeNEAAAQBAJ", "Lido", 5.0),
    ("u7", "3J_NAAAAQBAJ", "Lendo", None),
    ("u8", "8U2oAAAAQBAJ", "Lido", 5.0),
    ("u8", "1EiJAwAAQBAJ", "Lido", 4.0),
    ("u8", "FmyBCwAAQBAJ", "Quero ler", None),
    ("u10-teen", "vNxMMQEACAAJ", "Lido", 5.0),
    ("u11-crianca", "pD6arNyKyi8C", "Lido", 5.0),
    # sem consentimento: estas leituras não podem influenciar ninguém
    ("u12-sem-consentimento", "AoRbAAAAMAAJ", "Lido", 5.0),
    ("u12-sem-consentimento", "3J_NAAAAQBAJ", "Lido", 5.0),
    ("u12-sem-consentimento", "mock-hailmary", "Lido", 5.0),
]

INTERACTIONS: list[Interaction] = [Interaction(u, b, s, r) for u, b, s, r in _SHELF]
