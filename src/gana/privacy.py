"""Regras de privacidade e de classificação etária (spec 005).

Decisões técnicas inspiradas na LGPD (arts. 6º, 7º, 8º, 14, 18 e 46) e no ECA.
Não é parecer jurídico; ver docs/LGPD.md.
"""

from __future__ import annotations

import hashlib
from datetime import date

from gana.domain import Book, User

ADULT_AGE = 18
CHILD_AGE = 12  # ECA: criança até 12 anos incompletos

# segunda barreira, além do maturityRating do Google Books (que é autodeclarado)
SENSITIVE_CATEGORIES = {"erotica", "erotic", "erotic fiction", "adult fiction", "sexuality"}


def age_on(birth_date: date | None, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    today = today or date.today()
    before_birthday = (today.month, today.day) < (birth_date.month, birth_date.day)
    return today.year - birth_date.year - int(before_birthday)


def age_band(user: User, today: date | None = None) -> str:
    age = age_on(user.birth_date, today)
    if age is None:
        return "desconhecida"
    if age < CHILD_AGE:
        return "crianca"
    return "adolescente" if age < ADULT_AGE else "adulto"


def treat_as_minor(user: User | None, today: date | None = None) -> bool:
    """Para filtro de conteúdo, idade desconhecida conta como menor (padrão mais protetivo)."""
    if user is None:
        return True
    age = age_on(user.birth_date, today)
    return age is None or age < ADULT_AGE


def may_personalize(user: User, today: date | None = None) -> bool:
    """Consentimento é obrigatório; para crianças, também o dos responsáveis."""
    if not user.personalization_consent:
        return False
    age = age_on(user.birth_date, today)
    return not (age is not None and age < CHILD_AGE and not user.parental_consent)


def is_sensitive(book: Book) -> bool:
    if book.maturity_rating == "MATURE":
        return True
    categories = {c.lower() for c in [book.main_category, *book.categories]}
    return bool(categories & SENSITIVE_CATEGORIES)


def content_allowed(book: Book, user: User | None, today: date | None = None) -> bool:
    return not (treat_as_minor(user, today) and is_sensitive(book))


def pseudonymize(user_id: str, salt: str) -> str:
    """Identificador estável para logs, sem expor o UUID."""
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()[:12]
