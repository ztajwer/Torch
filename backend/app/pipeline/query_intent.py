from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.pipeline.search_match import _tokens, normalize_query, relevance_score, title_matches_query


@dataclass
class QueryIntent:
    original: str
    required_groups: list[list[str]] = field(default_factory=list)
    boost_terms: list[str] = field(default_factory=list)
    penalty_terms: list[str] = field(default_factory=list)
    category_hint: str = ""


# Penalize craft/measuring items when user wants drinkware, fashion, etc.
_CRAFT_CUP_PENALTIES = (
    "measuring cup",
    "measuring",
    "resin",
    "epoxy",
    "silicone",
    "50ml",
    "50 ml",
    "100ml",
    "diy",
    "craft",
    "uv resin",
    "baking cup",
    "mixing cup",
    "multipurpose silicone",
)

_DRINKWARE_BOOST = (
    "mug",
    "coffee cup",
    "tea cup",
    "ceramic",
    "glass cup",
    "drinking",
    "tumbler",
    "cup set",
    "coffee mug",
    "tea mug",
    "aesthetic",
    "kawaii",
    "cute",
    "minimalist",
    "stylish",
    "insulated",
)


def expand_search_queries(query: str) -> list[str]:
    """Extra store searches to improve intent (e.g. aesthetic cup → also aesthetic mug)."""
    q = normalize_query(query)
    if not q:
        return []
    out = [q.strip()]
    intent = analyze_query_intent(q)
    if intent.category_hint == "drinkware":
        if "cup" in q and "mug" not in q:
            alt = re.sub(r"\bcup\b", "mug", q)
            if alt != q:
                out.append(alt)
        if "mug" in q and "cup" not in q:
            alt = re.sub(r"\bmug\b", "cup", q)
            if alt != q:
                out.append(alt)
    if intent.category_hint == "bed_furniture":
        for alt in ("double bed", "single bed", "wooden bed", "folding bed", "charpai", "metal bed", "bed frame"):
            if alt not in out:
                out.append(alt)
    seen: set[str] = set()
    unique: list[str] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def analyze_query_intent(query: str) -> QueryIntent:
    q = normalize_query(query)
    tokens = _tokens(q)
    intent = QueryIntent(original=q, required_groups=[])

    if not tokens:
        intent.required_groups = [[q]] if q else []
        return intent

    # Default: every search word must appear (handled by title_matches_query).
    intent.required_groups = [[t] for t in tokens]

    if "cup" in tokens or "mug" in tokens:
        intent.category_hint = "drinkware"
        intent.boost_terms = list(_DRINKWARE_BOOST)
        intent.penalty_terms = list(_CRAFT_CUP_PENALTIES)
        # Also accept mug titles when user said cup
        if "cup" in tokens and "mug" not in tokens:
            intent.boost_terms.extend(["mug", "coffee mug", "tea mug"])

    if "aesthetic" in tokens:
        intent.boost_terms.extend(["aesthetic", "cute", "kawaii", "minimalist", "stylish", "designer", "deco"])

    if "iphone" in tokens:
        intent.category_hint = "mobile_phone"
        intent.boost_terms.extend(
            (
                "apple iphone",
                "iphone 11",
                "iphone 12",
                "iphone 13",
                "iphone 14",
                "iphone 15",
                "iphone 16",
                "128gb",
                "256gb",
                "512gb",
                "pre owned",
                "refurbished",
                "non pta",
                "pta approved",
            )
        )
        intent.penalty_terms.extend(_PHONE_ACCESSORY_PENALTIES)
    elif "phone" in tokens or "mobile" in tokens or any(
        b in tokens for b in _PHONE_BRANDS if b != "iphone"
    ):
        intent.category_hint = "mobile_phone"
        intent.penalty_terms.extend(_PHONE_ACCESSORY_PENALTIES)

    if "laptop" in tokens or "notebook" in tokens:
        intent.category_hint = "laptop"
        intent.penalty_terms.extend(["bag only", "sleeve only", "skin only", "sticker"])

    if "bed" in tokens and len(tokens) == 1 and tokens[0] == "bed":
        intent.category_hint = "bed_furniture"
        intent.boost_terms.extend(_BED_FURNITURE_BOOST)
        intent.penalty_terms.extend(_BEDDING_PENALTIES)
    elif "bed" in tokens:
        intent.category_hint = "bedroom"
        intent.boost_terms.extend(["bed frame", "mattress", "charpai", "folding bed"])
        intent.penalty_terms.extend(_BEDDING_PENALTIES)

    if "sofa" in tokens and len(tokens) == 1:
        intent.category_hint = "sofa_furniture"
        intent.boost_terms.extend(["sofa", "couch", "settee", "sofa set", "lounge"])
        intent.penalty_terms.extend(["sofa cover only", "cushion cover only", "slipcover"])

    return intent


_BEDDING_PENALTIES = (
    "bedsheet",
    "bed sheet",
    "bedsheets",
    "bedding",
    "bed linen",
    "pillow cover",
    "pillowcase",
    "pillow case",
    "duvet",
    "quilt cover",
    "comforter",
    "fitted sheet",
    "flat sheet",
    "bed spread",
    "bedspread",
    "mattress protector",
    "mattress cover",
    "bed cover set",
    "bedding set",
    "sheet set",
)

_PHONE_BRANDS = frozenset(
    {
        "iphone",
        "samsung",
        "redmi",
        "infinix",
        "oppo",
        "vivo",
        "realme",
        "pixel",
        "oneplus",
        "huawei",
        "poco",
        "nokia",
        "itel",
        "tecno",
    }
)

_PHONE_ACCESSORY_PENALTIES = (
    "phone case",
    "mobile case",
    "back cover",
    "screen protector",
    "tempered glass",
    "charging cable",
    "data cable",
    "charger",
    "power bank",
    "earphone",
    "headphone",
    "airpods",
    "tracker",
    "anti-lost",
    "bluetooth tag",
    "key finder",
    "for iphone",
    "compatible with iphone",
    "compatible with apple",
    "pretend play",
    "toy phone",
    "kids mobile",
    "wiphone",
    "phone holder",
    "selfie stick",
    "replacement screen",
    "display for",
    "battery for",
)

_IPHONE_MODEL_RE = re.compile(
    r"\biphone\s*("
    r"se(?:\s*\(?\s*(?:2nd|3rd)\s*gen\s*\)?)?|"
    r"(?:1[0-6](?:\s*(?:pro\s*max|pro|plus|max|mini|ultra))?|"
    r"x[rs]?(?:\s*max)?|"
    r"\d{1,2}))"
    r"(?:\s*\d{2,4}\s*gb)?",
    re.IGNORECASE,
)

_BED_FURNITURE_BOOST = (
    "wooden bed",
    "metal bed",
    "double bed",
    "single bed",
    "king size bed",
    "queen bed",
    "folding bed",
    "charpai",
    "charpoy",
    "charpay",
    "bed frame",
    "platform bed",
    "hospital bed",
    "wrought iron bed",
    "iron bed",
    "bunk bed",
    "storage bed",
    "space saving bed",
)


def is_smartphone_brand_query(query: str) -> bool:
    tokens = _tokens(query)
    if not tokens:
        return False
    if tokens in (["phone"], ["mobile"]):
        return True
    return bool(set(tokens) & _PHONE_BRANDS)


def _primary_phone_brand(query: str) -> str | None:
    tokens = _tokens(query)
    for brand in _PHONE_BRANDS:
        if brand in tokens:
            return brand
    if tokens in (["phone"], ["mobile"]):
        return "generic"
    return None


def _has_iphone_model(hay: str) -> bool:
    if _IPHONE_MODEL_RE.search(hay):
        return True
    if re.search(r"\bapple\s+iphone\b", hay, re.I) and re.search(r"\d+\s*gb", hay, re.I):
        return True
    return False


def is_phone_accessory(title: str) -> bool:
    """Cases, cables, trackers, toys — not the handset."""
    hay = _title_lower(title)

    if "wiphone" in hay or "wi-phone" in hay:
        return True
    if any(x in hay for x in ("pretend play", "toy phone", "kids mobile phone", "musical kids")):
        return True

    accessory_nouns = (
        "phone case",
        "mobile case",
        "back cover",
        "bumper case",
        "flip cover",
        "screen protector",
        "tempered glass",
        "camera protector",
        "camera lens guard",
        "charging cable",
        "data cable",
        "usb cable",
        "lightning cable",
        "wireless charger",
        "wall charger",
        "power adapter",
        "power bank",
        "earphones",
        "earphone",
        "headphone",
        "headset",
        "airpods",
        "anti-lost",
        "bluetooth tag",
        "gps tag",
        "key finder",
        "smart tag",
        "airtag",
        "phone holder",
        "car holder",
        "ring holder",
        "pop socket",
        "selfie stick",
        "sim ejector",
        "replacement screen",
        "lcd for",
        "display for",
        "touch screen for",
        "battery for",
        "flex cable",
        "charging port",
        "magsafe case",
        "magnetic case",
        "leather case",
        "silicone case",
    )
    if any(n in hay for n in accessory_nouns):
        return True

    if re.search(r"\b(for|compatible with|fits|supports)\s+(apple\s+)?iphone\b", hay):
        return True
    if re.search(r"\biphone\s+(ios\s+)?devices?\b", hay):
        return True

    if "iphone" in hay and not _has_iphone_model(hay):
        weak = ("case", "cover", "protector", "cable", "charger", "adapter", "tracker", "tag", "finder", "holder")
        if any(w in hay for w in weak):
            return True

    if "samsung" in hay or "galaxy" in hay:
        if any(x in hay for x in ("case for", "cover for", "compatible with", "screen guard for")):
            return True

    return False


def is_actual_smartphone(title: str, query: str) -> bool:
    """True when the listing is the phone itself, not an accessory or toy."""
    if not title_matches_query(title, query):
        return False
    if is_phone_accessory(title):
        return False

    hay = _title_lower(title)
    brand = _primary_phone_brand(query)

    if brand == "iphone" or "iphone" in _tokens(query):
        if "iphone" not in hay:
            return False
        return _has_iphone_model(hay)

    if brand == "samsung":
        if "galaxy" not in hay and "samsung" not in hay:
            return False
        return bool(
            re.search(r"\bgalaxy\s+[a-z]?\d{2,3}\b", hay, re.I)
            or re.search(r"\b(s24|s23|s22|a\d{2}|note\s*\d+|z\s*fold|z\s*flip)\b", hay, re.I)
            or (re.search(r"\d+\s*gb", hay) and "samsung" in hay)
        )

    if brand == "generic":
        return bool(re.search(r"\d+\s*gb", hay)) and any(b in hay for b in _PHONE_BRANDS)

    if brand and brand in hay:
        return bool(re.search(r"\d+\s*gb", hay)) or bool(re.search(rf"\b{re.escape(brand)}\s+\w+", hay))

    return True


def is_bedding_product(title: str) -> bool:
    hay = _title_lower(title)
    if any(p in hay for p in _BEDDING_PENALTIES):
        return True
    if "bedding" in hay and not any(f in hay for f in _BED_FURNITURE_BOOST):
        return True
    if "pillow" in hay and "bed" not in hay.replace("bedsheet", ""):
        if not any(f in hay for f in _BED_FURNITURE_BOOST):
            return True
    return False


def is_bed_furniture_title(title: str) -> bool:
    hay = _title_lower(title)
    if is_bedding_product(title):
        return False
    if any(f in hay for f in _BED_FURNITURE_BOOST):
        return True
    if re.search(r"\bbed\b", hay) and not is_bedding_product(title):
        if any(x in hay for x in ("frame", "wooden", "metal", "folding", "charpai", "charpoy", "bunk", "platform")):
            return True
        if "mattress" in hay and "sheet" not in hay and "cover" not in hay:
            return True
    return False


def title_matches_shopper_intent(title: str, query: str) -> bool:
    """Title gate: search words + category intent (bed ≠ bedsheet)."""
    from app.pipeline.search_match import title_matches_query

    tokens = _tokens(query)

    if tokens == ["bed"]:
        return is_bed_furniture_title(title)

    if tokens == ["sofa"]:
        hay = _title_lower(title)
        if any(x in hay for x in ("sofa cover", "cushion cover only", "slipcover only")):
            return False
        return "sofa" in hay or "couch" in hay or title_matches_query(title, query)

    if is_smartphone_brand_query(query):
        return is_actual_smartphone(title, query)

    return title_matches_query(title, query)


def product_matches_pipeline(
    title: str,
    query: str,
    *,
    expanded_queries: list[str] | None = None,
) -> bool:
    """
    Match the user's query and optional expanded scrape terms.
    Expanded terms like "double bed" must not admit bedsheets that only mention bed in linen titles.
    """
    if title_matches_shopper_intent(title, query):
        return True
    if not expanded_queries:
        return False
    q_norm = normalize_query(query)
    bed_search = _tokens(query) == ["bed"]
    for sq in expanded_queries:
        if normalize_query(sq) == q_norm:
            continue
        if not title_matches_query(title, sq):
            continue
        if bed_search:
            if is_bed_furniture_title(title):
                return True
            continue
        if is_smartphone_brand_query(query):
            if is_actual_smartphone(title, query):
                return True
            continue
        if title_matches_shopper_intent(title, sq):
            return True
    return False


def _title_lower(title: str) -> str:
    return (title or "").lower()


def intent_relevance_percent(title: str, query: str, intent: QueryIntent | None = None) -> float:
    """0–100: how well the product matches what the shopper likely wants."""
    if not title:
        return 0.0
    intent = intent or analyze_query_intent(query)
    hay = _title_lower(title)

    if not title_matches_shopper_intent(title, query):
        return 0.0

    base = relevance_score(title, query) * 55.0 if title_matches_query(title, query) else 45.0
    score = base + 20.0  # passed title gate

    for term in intent.boost_terms:
        if term in hay:
            score += 8.0

    for term in intent.penalty_terms:
        if term in hay:
            score -= 35.0

    # Drinkware: strong penalty for ml + silicone without mug/coffee/tea
    if intent.category_hint == "drinkware":
        if any(x in hay for x in ("measuring", "resin", "epoxy", "silicone", "50ml", "100ml")):
            if not any(x in hay for x in ("mug", "coffee", "tea", "ceramic", "glass", "tumbler", "drinking")):
                score -= 45.0

    if intent.category_hint == "bed_furniture":
        if is_bedding_product(title):
            return 0.0
        if is_bed_furniture_title(title):
            score += 35.0
        elif re.search(r"\bbed\b", hay):
            score -= 40.0

    if intent.category_hint == "mobile_phone":
        if is_phone_accessory(title):
            return 0.0
        if is_actual_smartphone(title, query):
            score += 40.0
            if _has_iphone_model(hay):
                score += 10.0
        else:
            score -= 50.0

    return max(0.0, min(100.0, round(score, 1)))


def value_score_percent(product: dict, relevance: float, *, query: str = "") -> float:
    """0–100 value score from price, rating, reviews, and relevance."""
    price = float(product.get("price") or 0)
    rating = float(product.get("rating") or 0)
    reviews = int(product.get("review_count") or 0)
    intent = analyze_query_intent(query) if query else None

    price_part = 30.0
    if price > 0:
        if intent and intent.category_hint == "mobile_phone":
            # Real phones in PK cost tens of thousands; cheap listings are usually accessories.
            if price < 15_000:
                price_part = 8.0
            elif 25_000 <= price <= 600_000:
                price_part = 32.0
            elif price > 600_000:
                price_part = 22.0
            else:
                price_part = 18.0
        elif price < 150:
            price_part = 15.0
        elif price > 50_000:
            price_part = 20.0
        else:
            price_part = 28.0

    rating_part = min(25.0, rating * 5.0) if rating > 0 else 10.0
    review_part = min(15.0, (reviews**0.5) * 2.0) if reviews > 0 else 5.0
    rel_part = relevance * 0.30

    return max(0.0, min(100.0, round(price_part + rating_part + review_part + rel_part, 1)))


def score_product(product: dict, query: str, intent: QueryIntent | None = None) -> dict:
    intent = intent or analyze_query_intent(query)
    title = str(product.get("product_title") or "")
    rel = intent_relevance_percent(title, query, intent)
    val = value_score_percent(product, rel, query=query)
    combined = rel * 0.62 + val * 0.38
    return {
        **product,
        "intent_relevance": rel,
        "shopper_value_score": val,
        "rank_score": round(combined, 2),
    }


def rank_products_by_intent(products: list[dict], query: str, *, min_relevance: float = 25.0) -> list[dict]:
    intent = analyze_query_intent(query)
    scored = [score_product(p, query, intent) for p in products]
    scored = [p for p in scored if p.get("intent_relevance", 0) >= min_relevance]
    scored.sort(
        key=lambda p: (
            p.get("rank_score", 0),
            p.get("intent_relevance", 0),
            -float(p.get("price") or 0),
        ),
        reverse=True,
    )
    return scored


def filter_for_display(products: list[dict], query: str) -> list[dict]:
    """All title matches, sorted by intent (weak matches sink to bottom)."""
    intent = analyze_query_intent(query)
    scored = [
        score_product(p, query, intent)
        for p in products
        if title_matches_shopper_intent(str(p.get("product_title") or ""), query)
    ]
    scored.sort(key=lambda p: (p.get("rank_score", 0), p.get("intent_relevance", 0)), reverse=True)
    return scored


def pick_top_for_recommendations(products: list[dict], query: str, limit: int = 3) -> list[dict]:
    intent = analyze_query_intent(query)
    min_rel = 50.0 if intent.category_hint == "mobile_phone" else 35.0
    ranked = rank_products_by_intent(products, query, min_relevance=min_rel)
    if len(ranked) < limit:
        ranked = rank_products_by_intent(products, query, min_relevance=25.0 if min_rel >= 50 else 15.0)
    return ranked[:limit]


def build_shopping_insights(query: str, products: list[dict], top_pick: dict | None) -> dict[str, Any]:
    if not products:
        return {}

    pool = rank_products_by_intent(products, query, min_relevance=30.0) or products
    prices = [float(p.get("price") or 0) for p in pool if float(p.get("price") or 0) > 0]
    cheapest = min(pool, key=lambda p: float(p.get("price") or 1e18)) if prices else None
    premium = max(pool, key=lambda p: float(p.get("price") or 0)) if prices else None

    insights: dict[str, Any] = {
        "total_matches": len(products),
        "cheapest": _brief(cheapest) if cheapest else None,
        "premium": _brief(premium) if premium else None,
    }

    if top_pick:
        rel = top_pick.get("intent_relevance", 0)
        val = top_pick.get("shopper_value_score") or top_pick.get("value_score") or 0
        insights["top_pick_relevance"] = rel
        insights["top_pick_value_score"] = val
        insights["why_number_one"] = (
            f"Out of {len(products)} relevant matches for '{query}', this is #1 with "
            f"{rel:.0f}% relevance (what you likely want) and {val:.0f}/100 value score. "
            f"Cheapest in this list: {_price_label(cheapest)}. "
        )
        if premium and premium.get("id") != top_pick.get("id"):
            insights["why_number_one"] += f"Premium option: {_price_label(premium)}."

    intent = analyze_query_intent(query)
    if intent.category_hint == "drinkware":
        insights["intent_note"] = (
            "We prioritized mugs, coffee/tea cups, and aesthetic drinkware — not measuring or resin craft cups."
        )
    if intent.category_hint == "bed_furniture":
        insights["intent_note"] = (
            "We prioritized actual beds, charpai, and bed frames — not bedsheets, pillows, or bedding sets."
        )
    if intent.category_hint == "mobile_phone":
        insights["intent_note"] = (
            "We prioritized actual smartphones (iPhone, Galaxy, etc.) — not cases, cables, trackers, or toy phones."
        )

    return insights


def _price_label(p: dict | None) -> str:
    if not p:
        return "—"
    from app.scrapers.sources.pk_utils import format_pkr

    return f"{format_pkr(p.get('price'))} ({p.get('marketplace', '')})"


def _brief(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "product_title": p.get("product_title"),
        "price": p.get("price"),
        "marketplace": p.get("marketplace"),
        "intent_relevance": p.get("intent_relevance"),
    }
