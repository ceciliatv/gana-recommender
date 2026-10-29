"""
Dados mockados espelhando o modelo real do banco de dados do app Gana.

Tabelas simuladas:
  - users       → tabela `user` do Supabase (sem email, auth é do Supabase)
  - books       → tabela `book_cache` (livros vindos do Google Books API)
  - user_books  → tabela `user_book` (relação usuário-livro com status)
  - reviews     → tabela `Post_Review` (avaliações com rate Float)

A função `get_interactions()` combina user_books + reviews para gerar
o sinal de rating que o algoritmo consome:
  - Lido + review  → usa o rate da review
  - Lido sem review → rating implícito 3.5
  - Lendo          → rating implícito 3.0 (engajamento positivo)
  - Quero ler      → rating implícito 2.0 (intenção, sinal fraco)
  - Abandonado     → rating implícito 1.0 (sinal negativo)
"""

# ── users (tabela `user`) ────────────────────────────────────────────────────

USERS = [
    {"user_id": "u1", "username": "ana_reads",    "name": "Ana",    "is_private": False},
    {"user_id": "u2", "username": "brunoscifi",   "name": "Bruno",  "is_private": False},
    {"user_id": "u3", "username": "carla.books",  "name": "Carla",  "is_private": False},
    {"user_id": "u4", "username": "diegohist",    "name": "Diego",  "is_private": False},
    {"user_id": "u5", "username": "elena_leitora","name": "Elena",  "is_private": False},
    {"user_id": "u6", "username": "felipe42",     "name": "Felipe", "is_private": False},
    {"user_id": "u7", "username": "gabi.mystery", "name": "Gabi",   "is_private": False},
    {"user_id": "u8", "username": "hugo_leitor",  "name": "Hugo",   "is_private": False},
]

# ── book_cache (livros vindos do Google Books, armazenados localmente) ───────

BOOKS = [
    {
        "book_id": "b101",
        "google_books_id": "gcfGnQEACAAJ",
        "isbn": "9788599296578",
        "title": "O Nome do Vento",
        "author": ["Patrick Rothfuss"],
        "pages": 662,
        "year_published": 2007,
        "publisher": "DAW Books",
        "main_category": "Fantasy",
        "categories": ["Fantasy", "Fiction", "Epic Fantasy"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=gcfGnQEACAAJ",
    },
    {
        "book_id": "b102",
        "google_books_id": "ydQiAQAAIAAJ",
        "isbn": "9780441013593",
        "title": "Duna",
        "author": ["Frank Herbert"],
        "pages": 412,
        "year_published": 1965,
        "publisher": "Chilton Books",
        "main_category": "Science Fiction",
        "categories": ["Science Fiction", "Fiction", "Classic Sci-Fi"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=ydQiAQAAIAAJ",
    },
    {
        "book_id": "b103",
        "google_books_id": "vNxMMQEACAAJ",
        "isbn": "9788544001820",
        "title": "Orgulho e Preconceito",
        "author": ["Jane Austen"],
        "pages": 432,
        "year_published": 1813,
        "publisher": "T. Egerton",
        "main_category": "Romance",
        "categories": ["Romance", "Classic Literature", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=vNxMMQEACAAJ",
    },
    {
        "book_id": "b104",
        "google_books_id": "AoRbAAAAMAAJ",
        "isbn": "9780385504201",
        "title": "O Código Da Vinci",
        "author": ["Dan Brown"],
        "pages": 454,
        "year_published": 2003,
        "publisher": "Doubleday",
        "main_category": "Thriller",
        "categories": ["Thriller", "Mystery", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=AoRbAAAAMAAJ",
    },
    {
        "book_id": "b105",
        "google_books_id": "1EiJAwAAQBAJ",
        "isbn": "9780062316097",
        "title": "Sapiens",
        "author": ["Yuval Noah Harari"],
        "pages": 443,
        "year_published": 2011,
        "publisher": "Harper",
        "main_category": "History",
        "categories": ["History", "Non-Fiction", "Anthropology"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=1EiJAwAAQBAJ",
    },
    {
        "book_id": "b106",
        "google_books_id": "pD6arNyKyi8C",
        "isbn": "9780547928227",
        "title": "O Hobbit",
        "author": ["J.R.R. Tolkien"],
        "pages": 310,
        "year_published": 1937,
        "publisher": "Allen & Unwin",
        "main_category": "Fantasy",
        "categories": ["Fantasy", "Fiction", "Adventure"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=pD6arNyKyi8C",
    },
    {
        "book_id": "b107",
        "google_books_id": "B4YGAQAAIAAJ",
        "isbn": "9780553293357",
        "title": "Fundação",
        "author": ["Isaac Asimov"],
        "pages": 244,
        "year_published": 1951,
        "publisher": "Gnome Press",
        "main_category": "Science Fiction",
        "categories": ["Science Fiction", "Classic Sci-Fi", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=B4YGAQAAIAAJ",
    },
    {
        "book_id": "b108",
        "google_books_id": "HMeNEAAAQBAJ",
        "isbn": "9781594633669",
        "title": "A Garota no Trem",
        "author": ["Paula Hawkins"],
        "pages": 336,
        "year_published": 2015,
        "publisher": "Riverhead Books",
        "main_category": "Thriller",
        "categories": ["Thriller", "Mystery", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=HMeNEAAAQBAJ",
    },
    {
        "book_id": "b109",
        "google_books_id": "yO9EAQAAMAAJ",
        "isbn": "9780140439083",
        "title": "Sherlock Holmes",
        "author": ["Arthur Conan Doyle"],
        "pages": 307,
        "year_published": 1892,
        "publisher": "George Newnes",
        "main_category": "Mystery",
        "categories": ["Mystery", "Classic Literature", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=yO9EAQAAMAAJ",
    },
    {
        "book_id": "b110",
        "google_books_id": "8U2oAAAAQBAJ",
        "isbn": "9781451648539",
        "title": "Steve Jobs",
        "author": ["Walter Isaacson"],
        "pages": 656,
        "year_published": 2011,
        "publisher": "Simon & Schuster",
        "main_category": "Biography",
        "categories": ["Biography", "Non-Fiction", "Technology"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=8U2oAAAAQBAJ",
    },
    {
        "book_id": "b111",
        "google_books_id": "FmOcAQAAQBAJ",
        "isbn": "9780553103540",
        "title": "A Guerra dos Tronos",
        "author": ["George R.R. Martin"],
        "pages": 694,
        "year_published": 1996,
        "publisher": "Bantam Books",
        "main_category": "Fantasy",
        "categories": ["Fantasy", "Fiction", "Epic Fantasy"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=FmOcAQAAQBAJ",
    },
    {
        "book_id": "b112",
        "google_books_id": "kotPYEqx7kMC",
        "isbn": "9780451524935",
        "title": "1984",
        "author": ["George Orwell"],
        "pages": 328,
        "year_published": 1949,
        "publisher": "Secker & Warburg",
        "main_category": "Science Fiction",
        "categories": ["Science Fiction", "Dystopia", "Classic Literature"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=kotPYEqx7kMC",
    },
    {
        "book_id": "b113",
        "google_books_id": "ExkMAAAAYAAJ",
        "isbn": "9780141439556",
        "title": "O Morro dos Ventos Uivantes",
        "author": ["Emily Brontë"],
        "pages": 342,
        "year_published": 1847,
        "publisher": "Thomas Newby",
        "main_category": "Romance",
        "categories": ["Romance", "Classic Literature", "Gothic Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=ExkMAAAAYAAJ",
    },
    {
        "book_id": "b114",
        "google_books_id": "3J_NAAAAQBAJ",
        "isbn": "9780385537858",
        "title": "Inferno",
        "author": ["Dan Brown"],
        "pages": 480,
        "year_published": 2013,
        "publisher": "Doubleday",
        "main_category": "Thriller",
        "categories": ["Thriller", "Mystery", "Fiction"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=3J_NAAAAQBAJ",
    },
    {
        "book_id": "b115",
        "google_books_id": "FmyBCwAAQBAJ",
        "isbn": "9780062464316",
        "title": "Homo Deus",
        "author": ["Yuval Noah Harari"],
        "pages": 450,
        "year_published": 2015,
        "publisher": "Harvill Secker",
        "main_category": "History",
        "categories": ["History", "Non-Fiction", "Futurism"],
        "language": "pt",
        "url_image": "https://books.google.com/thumbnail?id=FmyBCwAAQBAJ",
    },
]

# ── user_book (relação usuário-livro com status) ─────────────────────────────
# status: "Quero ler" | "Lendo" | "Lido" | "Abandonado"

USER_BOOKS = [
    # Ana: fantasy e romance
    {"user_id": "u1", "book_id": "b101", "status": "Lido"},
    {"user_id": "u1", "book_id": "b106", "status": "Lido"},
    {"user_id": "u1", "book_id": "b111", "status": "Lido"},
    {"user_id": "u1", "book_id": "b103", "status": "Lido"},
    {"user_id": "u1", "book_id": "b113", "status": "Lendo"},
    # Bruno: sci-fi e thriller
    {"user_id": "u2", "book_id": "b102", "status": "Lido"},
    {"user_id": "u2", "book_id": "b107", "status": "Lido"},
    {"user_id": "u2", "book_id": "b112", "status": "Lido"},
    {"user_id": "u2", "book_id": "b104", "status": "Lido"},
    {"user_id": "u2", "book_id": "b108", "status": "Abandonado"},
    # Carla: fantasy e mystery
    {"user_id": "u3", "book_id": "b101", "status": "Lido"},
    {"user_id": "u3", "book_id": "b106", "status": "Lido"},
    {"user_id": "u3", "book_id": "b109", "status": "Lido"},
    {"user_id": "u3", "book_id": "b111", "status": "Lendo"},
    # Diego: history e biography
    {"user_id": "u4", "book_id": "b105", "status": "Lido"},
    {"user_id": "u4", "book_id": "b110", "status": "Lido"},
    {"user_id": "u4", "book_id": "b115", "status": "Lido"},
    # Elena: muito parecida com Ana
    {"user_id": "u5", "book_id": "b101", "status": "Lido"},
    {"user_id": "u5", "book_id": "b103", "status": "Lido"},
    {"user_id": "u5", "book_id": "b106", "status": "Lido"},
    {"user_id": "u5", "book_id": "b111", "status": "Lido"},
    {"user_id": "u5", "book_id": "b113", "status": "Lido"},
    # Felipe: sci-fi e history
    {"user_id": "u6", "book_id": "b102", "status": "Lido"},
    {"user_id": "u6", "book_id": "b107", "status": "Lido"},
    {"user_id": "u6", "book_id": "b105", "status": "Lido"},
    {"user_id": "u6", "book_id": "b112", "status": "Lido"},
    {"user_id": "u6", "book_id": "b115", "status": "Lendo"},
    # Gabi: mystery e thriller
    {"user_id": "u7", "book_id": "b109", "status": "Lido"},
    {"user_id": "u7", "book_id": "b104", "status": "Lido"},
    {"user_id": "u7", "book_id": "b108", "status": "Lido"},
    {"user_id": "u7", "book_id": "b114", "status": "Lendo"},
    # Hugo: biography e history
    {"user_id": "u8", "book_id": "b110", "status": "Lido"},
    {"user_id": "u8", "book_id": "b105", "status": "Lido"},
    {"user_id": "u8", "book_id": "b115", "status": "Quero ler"},
]

# ── Post_Review (avaliações explícitas — nem todo user_book tem review) ──────

REVIEWS = [
    {"user_id": "u1", "book_id": "b101", "rate": 5.0},
    {"user_id": "u1", "book_id": "b106", "rate": 4.0},
    {"user_id": "u1", "book_id": "b111", "rate": 5.0},
    {"user_id": "u1", "book_id": "b103", "rate": 4.0},

    {"user_id": "u2", "book_id": "b102", "rate": 5.0},
    {"user_id": "u2", "book_id": "b107", "rate": 5.0},
    {"user_id": "u2", "book_id": "b112", "rate": 4.0},
    {"user_id": "u2", "book_id": "b104", "rate": 4.0},

    {"user_id": "u3", "book_id": "b101", "rate": 4.0},
    {"user_id": "u3", "book_id": "b106", "rate": 5.0},
    {"user_id": "u3", "book_id": "b109", "rate": 5.0},

    {"user_id": "u4", "book_id": "b105", "rate": 5.0},
    {"user_id": "u4", "book_id": "b110", "rate": 4.0},
    {"user_id": "u4", "book_id": "b115", "rate": 5.0},

    {"user_id": "u5", "book_id": "b101", "rate": 5.0},
    {"user_id": "u5", "book_id": "b103", "rate": 5.0},
    {"user_id": "u5", "book_id": "b106", "rate": 4.0},
    {"user_id": "u5", "book_id": "b111", "rate": 4.0},
    {"user_id": "u5", "book_id": "b113", "rate": 5.0},

    {"user_id": "u6", "book_id": "b102", "rate": 4.0},
    {"user_id": "u6", "book_id": "b105", "rate": 5.0},
    {"user_id": "u6", "book_id": "b112", "rate": 5.0},

    {"user_id": "u7", "book_id": "b109", "rate": 5.0},
    {"user_id": "u7", "book_id": "b104", "rate": 4.0},
    {"user_id": "u7", "book_id": "b108", "rate": 5.0},

    {"user_id": "u8", "book_id": "b110", "rate": 5.0},
    {"user_id": "u8", "book_id": "b105", "rate": 4.0},
]

# ── Rating implícito por status (quando não há review explícita) ─────────────
_IMPLICIT_RATING = {
    "Lido":       3.5,
    "Lendo":      3.0,
    "Quero ler":  2.0,
    "Abandonado": 1.0,
}


def get_users():
    return USERS

def get_books():
    return BOOKS

def get_interactions():
    """
    Constrói o sinal de interação combinando user_book + reviews.
    Retorna lista de (user_id, book_id, rating) — mesmo contrato de antes.
    """
    review_map = {(r["user_id"], r["book_id"]): r["rate"] for r in REVIEWS}
    interactions = []
    for ub in USER_BOOKS:
        uid, bid = ub["user_id"], ub["book_id"]
        rating = review_map.get((uid, bid), _IMPLICIT_RATING[ub["status"]])
        interactions.append((uid, bid, rating))
    return interactions
