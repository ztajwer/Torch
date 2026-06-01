from __future__ import annotations

import math
from typing import Any, Optional

from app.pipeline.query_intent import rank_products_by_intent
from app.scrapers.sources.pk_utils import format_pkr, sanitize_pkr_price


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


def valid_priced_products(products: list[dict]) -> list[dict]:
    out: list[dict] = []
    for p in products:
        title = str(p.get("product_title") or "")
        price = sanitize_pkr_price(_safe_float(p.get("price")) or None, title)
        if price is None or price <= 0:
            continue
        out.append({**p, "price": price, "currency": "PKR"})
    return out


def _quality_score(p: dict) -> float:
    rating = _safe_float(p.get("rating"))
    reviews = _safe_int(p.get("review_count"))
    return (rating * 0.65) + (math.log(reviews + 1) * 0.35)


def _overall_score(p: dict) -> float:
    trend = _safe_float(p.get("trend_score"))
    value = _safe_float(p.get("best_value_score"))
    quality = _quality_score(p)
    price = _safe_float(p.get("price"))
    # Prefer reasonable PKR value: not the fake-cheapest RAM-digit prices.
    price_factor = 1.0 / (1.0 + math.log10(max(price, 500)))
    return (trend * 0.30) + (value * 1000.0 * 0.30) + (quality * 0.25) + (price_factor * 0.15)


def pick_recommendations(products: list[dict], query: str = "") -> dict[str, Any]:
    valid = valid_priced_products(products)
    if query:
        valid = rank_products_by_intent(valid, query, min_relevance=15.0) or valid
    if not valid:
        return {
            "best_overall": None,
            "cheapest": None,
            "best_quality": None,
            "summary": "No matching products with valid PKR prices found.",
        }

    rated = [p for p in valid if _safe_float(p.get("rating")) > 0]

    cheapest = min(valid, key=lambda p: _safe_float(p.get("price")))
    best_quality = max(rated or valid, key=_quality_score)
    best_overall = valid[0] if query and valid else max(valid, key=_overall_score)

    def brief(p: dict) -> dict:
        return {
            "id": p.get("id"),
            "product_title": p.get("product_title"),
            "marketplace": p.get("marketplace"),
            "price": p.get("price"),
            "currency": "PKR",
            "rating": p.get("rating"),
            "review_count": p.get("review_count"),
            "product_url": p.get("product_url"),
            "trend_score": p.get("trend_score"),
            "best_value_score": p.get("best_value_score"),
        }

    title = str(best_overall.get("product_title") or "this item")
    store = str(best_overall.get("marketplace") or "a store")
    price_txt = format_pkr(_safe_float(best_overall.get("price")))
    cheap_txt = format_pkr(_safe_float(cheapest.get("price")))

    summary = (
        f"We recommend {title} from {store} at {price_txt} — best balance of price and quality in Pakistan. "
        f"The lowest price we found is {cheap_txt}."
    )

    return {
        "best_overall": {**brief(best_overall), "reason": "Best price + quality for you."},
        "cheapest": {**brief(cheapest), "reason": "Lowest price found."},
        "best_quality": {**brief(best_quality), "reason": "Highest customer rating."},
        "summary": summary,
    }


def group_by_marketplace(products: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for p in valid_priced_products(products):
        m = str(p.get("marketplace") or "Unknown")
        out.setdefault(m, []).append(p)
    for m in out:
        out[m].sort(key=lambda x: _overall_score(x), reverse=True)
    return out


def compare_best(products: list[dict]) -> tuple[list[dict], Optional[str]]:
    valid = valid_priced_products(products)
    if not valid:
        return [], None
    best = max(
        valid,
        key=lambda p: (_overall_score(p), _safe_float(p.get("best_value_score")), _safe_float(p.get("rating"))),
    )
    return valid, str(best.get("id"))
