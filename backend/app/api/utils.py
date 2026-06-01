from __future__ import annotations

import math
from typing import Any, Iterable, Optional


def _safe_float(x: Any) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except Exception:
        return 0.0


def _safe_int(x: Any) -> int:
    try:
        return max(int(x), 0)
    except Exception:
        return 0


def text_match(haystack: str, needle: str) -> bool:
    return needle.lower() in (haystack or "").lower()


def apply_filters(
    products: list[dict],
    *,
    q: Optional[str] = None,
    category: Optional[str] = None,
    marketplace: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
) -> list[dict]:
    out = []
    for p in products:
        if q:
            from app.pipeline.search_match import title_matches_query

            title = str(p.get("product_title", ""))
            norm = str(p.get("normalized_title", ""))
            if not (title_matches_query(title, q) or title_matches_query(norm, q)):
                continue
        if category and (p.get("category") or "Uncategorized") != category:
            continue
        if marketplace and (p.get("marketplace") or "") != marketplace:
            continue

        price = _safe_float(p.get("price"))
        rating = _safe_float(p.get("rating"))

        if price_min is not None and price < float(price_min):
            continue
        if price_max is not None and price > float(price_max):
            continue
        if rating_min is not None and rating < float(rating_min):
            continue
        if rating_max is not None and rating > float(rating_max):
            continue

        out.append(p)
    return out


def apply_sort(products: list[dict], sort: str) -> list[dict]:
    s = (sort or "").strip()
    if s == "price_asc":
        return sorted(products, key=lambda p: _safe_float(p.get("price")))
    if s == "price_desc":
        return sorted(products, key=lambda p: _safe_float(p.get("price")), reverse=True)
    if s == "rating_desc":
        return sorted(products, key=lambda p: _safe_float(p.get("rating")), reverse=True)
    if s == "reviews_desc":
        return sorted(products, key=lambda p: _safe_int(p.get("review_count")), reverse=True)
    if s == "trend_desc":
        return sorted(products, key=lambda p: _safe_float(p.get("trend_score")), reverse=True)
    if s == "best_value_desc":
        return sorted(products, key=lambda p: _safe_float(p.get("best_value_score")), reverse=True)
    return products


def paginate(items: list[dict], *, offset: int, limit: int) -> dict:
    offset = max(int(offset), 0)
    limit = min(max(int(limit), 1), 10000)
    total = len(items)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": items[offset : offset + limit],
    }

