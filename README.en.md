<div align="center">

# Gana — Book Social Network (iOS)

**Hybrid recommendation engine** for Gana: the backend the app consumes.
Python · FastAPI · Supabase · Google Books API · cold start · LGPD (Brazil's data protection law) · age rating

[![CI](https://github.com/ceciliatv/gana-recommender/actions/workflows/ci.yml/badge.svg)](https://github.com/ceciliatv/gana-recommender/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Versão em português](README.md)

</div>

---

**Gana** is an iOS app (SwiftUI) where people build shelves ("Want to read", "Reading", "Read", "Abandoned"), write reviews and follow other readers. It was built as a team at the Apple Developer Academy | UNICAMP. This repository is the **recommendation service** the app consumes.

It started as a proof of concept ([first commit](https://github.com/ceciliatv/gana-recommender/commit/f8436b5)) and evolved through **spec-driven development** into:

- a **weighted hybrid** (collaborative + content + popularity) whose weights adapt to each person's history, based on Charu Aggarwal's *Recommender Systems: The Textbook*;
- layered **cold start** for newcomers and for books nobody has read yet;
- **Google Books API** integration to populate the catalog;
- **LGPD and age rating**: consent, data minimization, data-subject rights, JWT auth and an adult-content filter for minors;
- a **reproducible offline evaluation** on a public dataset in the app's schema, reported honestly (including where the engine loses).

## The engine

```
score = a · collaborative + (1 − a − g) · content + g · popularity
a = 0.3 · n / (n + 5)      collaborative weight grows with history, capped
g = 0.5 · 5 / (n + 5)      popularity prior fades as the person reads
```

- **Collaborative:** user-based, with judgments ("Read", "Abandoned", reviews) **centered on the person's mean**, so abandoning a book becomes a **negative** signal (in the POC it still counted as a like). Cosine on centered vectors, 20 nearest neighbors.
- **Content:** TF-IDF over main category (weight 2), categories and authors.
- **Bayesian popularity:** `log(1 + v) · (v·R + m·C) / (v + m)`.
- Every recommendation comes with **reasons** and the response states the **strategy** used.

**Cold start:** no consent → non-personalized popularity (age-filtered); 0 books → popularity, or half onboarding-genre content and half popularity; 1–4 books → hybrid whose content also uses onboarding genres; 5+ → hybrid with growing collaborative weight. New books enter through content.

## LGPD and age rating

Minimization (the service reads only id, birth date, consent flags and favorite genres; the POC's `GET /users`, which exposed everyone's names, was removed) · consent (without it, recommendations are generic **and the person's reads train no one's model**) · children under 12 need parental consent · under-18s and unknown ages never get `MATURE` books · `GET`/`DELETE /users/{id}/data` · Supabase JWT required when `SUPABASE_JWT_SECRET` is set (the token's `sub` must be the route's user) · pseudonymized logs. Details in [`docs/LGPD.md`](docs/LGPD.md) (Portuguese; not legal advice).

## Evaluation

Goodbooks-10k (CC BY-SA 4.0) converted to Gana's schema; 3,000 test users (seed 42); engine weights chosen on a **separate validation sample** (seed 7). Full ranking, no negative sampling.

**Leave-one-out** NDCG@10: popularity 0.0358 · collaborative 0.0457 · content 0.0527 · fixed-weight hybrid α = 0.5 (like the POC) 0.0576 · **adaptive hybrid 0.0592** (+65% over popularity).

**Cold start** Recall@20 with only k visible books:

| Strategy | k = 0 | k = 1 | k = 3 |
|---|---:|---:|---:|
| Popularity (count) | **0.2454** | **0.2437** | 0.2403 |
| Collaborative | — | 0.2238 | 0.2401 |
| **Layered (Gana)** | 0.2331 | 0.2264 | **0.2485** |

With 3 books the layered strategy is best, but **with 0 or 1 book plain popularity still wins** (by 5–7%): on Goodbooks a few books dominate every shelf. Onboarding genres stay in the engine so the first screen reflects what the person said they like; the measured cost of that choice is in the table.

## Running

```bash
pip install -e ".[dev,supabase]"
gana serve                 # http://127.0.0.1:8000/docs (synthetic data)
gana evaluate              # downloads Goodbooks-10k, writes reports/offline.md
gana ingest "dune" --dry-run
pytest                     # 58 tests, no network
```

The API keeps every path and field the iOS app already decodes; `strategy`, `alpha` and `reasons` are additive.

## Credits

The Gana iOS app was built as a team at the Apple Developer Academy | UNICAMP (the app repository is private). The recommendation engine, the API and this repository are by **Maria Cecília Torres Vianna** · [LinkedIn](https://linkedin.com/in/cecília-vianna-708a67285).
