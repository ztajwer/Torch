from __future__ import annotations

import re
from typing import Optional


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", (query or "").strip().lower())


def _tokens(query: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", normalize_query(query)) if len(t) >= 2]


def _whole_word(hay: str, token: str) -> bool:
    return bool(re.search(rf"\b{re.escape(token)}\b", hay, flags=re.IGNORECASE))


def relevance_score(title: str, query: str) -> float:
    """1.0 = exact phrase in title; lower = weaker match."""
    q = normalize_query(query)
    hay = (title or "").strip()
    if not q or not hay:
        return 0.0
    hay_l = hay.lower()
    if q in hay_l:
        return 1.0
    tokens = _tokens(q)
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if _whole_word(hay_l, t))
    return hits / len(tokens)


def title_matches_query(title: str, query: str, *, min_score: float = 1.0) -> bool:
    """
    Strict match: every search word must appear as a whole word in the product title.
    Prevents 'macbook' from matching category 'Books' or random 'book' substrings.
    """
    return relevance_score(title, query) >= min_score


def filter_products_for_query(products: list[dict], query: str) -> list[dict]:
    """Keep only products matching shopper intent; sort by relevance."""
    from app.pipeline.query_intent import filter_for_display, title_matches_shopper_intent

    q = (query or "").strip()
    if not q:
        return products
    matched = []
    for p in products:
        title = str(p.get("product_title") or "")
        norm = str(p.get("normalized_title") or "")
        if title_matches_shopper_intent(title, q) or title_matches_shopper_intent(norm, q):
            matched.append(p)
    return filter_for_display(matched, q)


def is_tech_product_query(query: str) -> bool:
    q = normalize_query(query)
    tech = {
        "phone",
        "iphone",
        "ipad",
        "macbook",
        "laptop",
        "notebook",
        "computer",
        "tablet",
        "watch",
        "earphone",
        "headphone",
        "camera",
        "tv",
        "monitor",
        "console",
        "playstation",
        "xbox",
    }
    tokens = set(_tokens(q))
    if tokens & tech:
        return True
    return any(t in q for t in tech)


def is_book_product_query(query: str) -> bool:
    q = normalize_query(query)
    if "book" in q or "novel" in q or "reading" in q:
        return True
    tokens = set(_tokens(q))
    return bool(tokens & {"book", "books", "novel", "poetry", "fiction"})
