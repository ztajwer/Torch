from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


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


def compute_scores(products: list[dict]) -> None:
    # Compute proxy sales_velocity using review_count growth is not available in JSON-only pipeline.
    # We use review_count as proxy directly and normalize within dataset.
    max_reviews = max((_safe_int(p.get("review_count")) for p in products), default=0)
    max_reviews = max(max_reviews, 1)

    prices = [_safe_float(p.get("price")) for p in products if _safe_float(p.get("price")) > 0]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 1.0
    if max_price <= 0:
        max_price = 1.0

    for p in products:
        rating = _safe_float(p.get("rating"))
        reviews = _safe_int(p.get("review_count"))

        # trend_score formula
        # rating * 0.4 + log(reviews+1)*0.3 + proxy_velocity*0.3
        proxy_velocity = reviews / max_reviews
        trend = (rating * 0.4) + (math.log(reviews + 1) * 0.3) + (proxy_velocity * 0.3)
        p["trend_score"] = round(float(trend), 5)

        price = _safe_float(p.get("price"))
        price_norm = (price - min_price) / (max_price - min_price) if (max_price - min_price) > 0 else 0.0
        # best_value_score = rating / price * normalization_factor
        normalization_factor = 1.0 + (1.0 - price_norm)  # cheaper => higher factor
        bv = 0.0
        if price > 0 and rating > 0:
            bv = (rating / price) * normalization_factor
        p["best_value_score"] = round(float(bv), 8)


def build_analytics(products: list[dict]) -> dict:
    compute_scores(products)

    def top_ids(key: str, n: int, *, reverse: bool = True) -> list[str]:
        return [
            p["id"]
            for p in sorted(products, key=lambda x: _safe_float(x.get(key)), reverse=reverse)[:n]
            if p.get("id")
        ]

    top_rated = [
        p["id"]
        for p in sorted(
            products,
            key=lambda x: (_safe_float(x.get("rating")), _safe_int(x.get("review_count"))),
            reverse=True,
        )[:20]
        if p.get("id")
    ]

    lowest_price = [
        p["id"]
        for p in sorted(products, key=lambda x: _safe_float(x.get("price")))[:20]
        if p.get("id")
    ]

    most_reviewed = [
        p["id"]
        for p in sorted(products, key=lambda x: _safe_int(x.get("review_count")), reverse=True)[:20]
        if p.get("id")
    ]

    trending = top_ids("trend_score", 20, reverse=True)
    best_value = top_ids("best_value_score", 20, reverse=True)

    # Marketplace rankings: weighted by avg trend + avg rating + volume
    by_market: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        by_market[str(p.get("marketplace") or "Unknown")].append(p)

    rankings = []
    for m, ps in by_market.items():
        avg_trend = sum(_safe_float(x.get("trend_score")) for x in ps) / max(len(ps), 1)
        avg_rating = sum(_safe_float(x.get("rating")) for x in ps) / max(len(ps), 1)
        volume = len(ps)
        score = (avg_trend * 0.55) + (avg_rating * 0.35) + (math.log(volume + 1) * 0.10)
        rankings.append(
            {
                "marketplace": m,
                "products": volume,
                "avg_trend_score": round(avg_trend, 4),
                "avg_rating": round(avg_rating, 4),
                "score": round(score, 5),
            }
        )
    rankings.sort(key=lambda x: x["score"], reverse=True)

    # Category distribution
    cats = Counter((p.get("category") or "Uncategorized") for p in products)
    category_distribution = [{"category": k, "count": v} for k, v in cats.most_common(25)]

    # Price distribution (bins)
    prices = sorted(_safe_float(p.get("price")) for p in products if _safe_float(p.get("price")) > 0)
    bins = []
    if prices:
        lo, hi = prices[0], prices[-1]
        steps = 8
        width = (hi - lo) / steps if hi > lo else 1.0
        for i in range(steps):
            a = lo + i * width
            b = lo + (i + 1) * width
            bins.append({"min": round(a, 2), "max": round(b, 2), "count": 0})
        for p in prices:
            idx = int((p - lo) / width) if width > 0 else 0
            idx = min(max(idx, 0), steps - 1)
            bins[idx]["count"] += 1

    totals = {"products": len(products)}
    kpis = {
        "avg_price": round(sum(prices) / len(prices), 2) if prices else 0.0,
        "avg_rating": round(
            (sum(_safe_float(p.get("rating")) for p in products) / max(len(products), 1)), 2
        ),
        "avg_trend_score": round(
            (sum(_safe_float(p.get("trend_score")) for p in products) / max(len(products), 1)), 4
        ),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": totals,
        "kpis": kpis,
        "top_rated_products": top_rated,
        "lowest_price_products": lowest_price,
        "most_reviewed_products": most_reviewed,
        "trending_products": trending,
        "best_value_products": best_value,
        "marketplace_rankings": rankings[:20],
        "category_distribution": category_distribution,
        "price_distribution": bins,
    }

