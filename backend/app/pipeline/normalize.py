from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime
from typing import Optional

from app.scrapers.base import RawProduct
from app.scrapers.sources.pk_utils import sanitize_pkr_price


_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]+")


def normalize_title(title: str) -> str:
    t = (title or "").strip().lower()
    t = _NON_ALNUM_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def compute_dedupe_key(normalized_title: str, category: Optional[str]) -> str:
    base = f"{normalized_title}|{(category or '').strip().lower()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def stable_product_id(marketplace: str, product_url: str) -> str:
    base = f"{marketplace}|{product_url}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:18]


def coerce_price(price: Optional[float]) -> Optional[float]:
    if price is None:
        return None
    try:
        p = float(price)
        if math.isnan(p) or math.isinf(p) or p < 0:
            return None
        return round(p, 2)
    except Exception:
        return None


def coerce_rating(r: Optional[float]) -> Optional[float]:
    if r is None:
        return None
    try:
        v = float(r)
        if math.isnan(v) or math.isinf(v):
            return None
        if v < 0:
            v = 0.0
        if v > 5:
            v = 5.0
        return round(v, 2)
    except Exception:
        return None


def to_unified_product(raw: RawProduct) -> dict:
    nt = normalize_title(raw.product_title)
    dedupe_key = compute_dedupe_key(nt, raw.category)
    pid = stable_product_id(raw.marketplace, raw.product_url)

    price = sanitize_pkr_price(coerce_price(raw.price), raw.product_title)
    original_price = sanitize_pkr_price(coerce_price(raw.original_price), raw.product_title)
    if price is None and original_price is not None:
        price = original_price

    rating = coerce_rating(raw.rating)
    review_count = raw.review_count if raw.review_count is None else max(int(raw.review_count), 0)

    return {
        "id": pid,
        "product_title": raw.product_title.strip() or "Unknown",
        "price": price or 0.0,
        "currency": "PKR",
        "original_price": original_price,
        "rating": rating,
        "review_count": review_count,
        "brand_or_seller": (raw.brand_or_seller.strip() if raw.brand_or_seller else None),
        "category": (raw.category.strip() if raw.category else None),
        "marketplace": raw.marketplace,
        "availability": (raw.availability.strip() if raw.availability else None),
        "product_url": raw.product_url,
        "image_url": raw.image_url,
        "timestamp_scraped": raw.timestamp_scraped.isoformat(),
        "normalized_title": nt,
        "dedupe_key": dedupe_key,
        "trend_score": 0.0,
        "best_value_score": 0.0,
    }


def choose_best_record(a: dict, b: dict) -> dict:
    # Prefer record with more filled fields + newer timestamp
    def score(p: dict) -> tuple[int, str]:
        filled = 0
        for k in ("rating", "review_count", "image_url", "availability", "category", "brand_or_seller"):
            if p.get(k) not in (None, "", 0):
                filled += 1
        ts = str(p.get("timestamp_scraped") or "")
        return (filled, ts)

    return b if score(b) >= score(a) else a


def deduplicate(products: list[dict]) -> list[dict]:
    # De-dupe across marketplaces by dedupe_key; keep best record but also keep marketplace-specific ones
    # Rule: for each dedupe_key keep best record as "canonical", plus keep per-marketplace entries.
    canonical: dict[str, dict] = {}
    out: list[dict] = []
    seen_id: set[str] = set()

    for p in products:
        pid = str(p.get("id", ""))
        if not pid or pid in seen_id:
            continue
        seen_id.add(pid)
        out.append(p)

        dk = str(p.get("dedupe_key", ""))
        if not dk:
            continue
        prev = canonical.get(dk)
        canonical[dk] = p if prev is None else choose_best_record(prev, p)

    # Attach canonical_id for comparisons/search grouping
    for p in out:
        dk = str(p.get("dedupe_key", ""))
        if dk and dk in canonical:
            p["canonical_id"] = canonical[dk]["id"]
        else:
            p["canonical_id"] = p["id"]
    return out

