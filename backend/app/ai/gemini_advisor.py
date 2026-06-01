from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from app.config import settings
from app.pipeline.query_intent import (
    analyze_query_intent,
    build_shopping_insights,
    pick_top_for_recommendations,
    rank_products_by_intent,
)
from app.pipeline.search_match import filter_products_for_query, title_matches_query
from app.scrapers.sources.pk_utils import format_pkr


log = logging.getLogger("torch.ai.gemini")

_PK_STORE_HINTS = ("PriceOye", "Daraz", "Telemart", "Shophive", "Mega.pk")
_DOLLAR_RE = re.compile(r"\$\s*[\d,.]+|\bUSD\b", re.I)


def _prefer_pk_products(products: list[dict]) -> list[dict]:
    pk = [p for p in products if any(h in (p.get("marketplace") or "") for h in _PK_STORE_HINTS)]
    return pk if pk else products


def _strip_dollar_text(text: str) -> str:
    return _DOLLAR_RE.sub("", text or "").strip()


def _ranking_from_product(p: dict, rank: int, reason: str) -> dict[str, Any]:
    return {
        "rank": rank,
        "product_id": p.get("id"),
        "title": p.get("product_title"),
        "marketplace": p.get("marketplace"),
        "price": p.get("price"),
        "currency": "PKR",
        "reason": _strip_dollar_text(reason),
        "product_url": p.get("product_url"),
        "image_url": p.get("image_url"),
        "rating": p.get("rating"),
        "relevance_percent": p.get("intent_relevance"),
        "value_score": p.get("shopper_value_score"),
    }


def build_ai_summary(query: str, rankings: list[dict], insights: dict[str, Any]) -> str:
    if not rankings:
        return f"No products with '{query}' in the title were found on Pakistani stores."

    top = rankings[0]
    total = insights.get("total_matches") or len(rankings)
    cheapest = insights.get("cheapest")
    cheap_txt = format_pkr(cheapest.get("price")) if cheapest else "—"
    premium = insights.get("premium")
    prem_txt = format_pkr(premium.get("price")) if premium else "—"

    rel = top.get("relevance_percent") or top.get("intent_relevance") or 0
    val = top.get("shopper_value_score") or top.get("value_score") or 0

    lines = [
        f"Best match for '{query}': {top.get('title')} at {format_pkr(top.get('price'))} on {top.get('marketplace')}.",
        f"Out of {total} matching products, this ranked #1 with {rel:.0f}% relevance and {val:.0f}/100 value score.",
        f"Cheapest option: {cheap_txt}. Premium option: {prem_txt}.",
    ]
    note = insights.get("intent_note")
    if note:
        lines.append(note)
    return " ".join(lines)


def _smart_rankings(query: str, products: list[dict]) -> dict[str, Any]:
    ranked = rank_products_by_intent(products, query, min_relevance=20.0)
    top3 = pick_top_for_recommendations(products, query, limit=3)
    if not top3:
        return {
            "summary": f"No strong matches for '{query}' after intent filtering.",
            "rankings": [],
            "insights": {},
            "powered_by": "torch-intent",
        }

    rankings = []
    reasons = [
        "Best match for what you searched — highest relevance and overall value.",
        "Strong alternative — good price and relevance.",
        "Also worth considering — rated well or great price.",
    ]
    for i, p in enumerate(top3):
        rankings.append(_ranking_from_product(p, i + 1, reasons[i] if i < len(reasons) else "Good option"))

    insights = build_shopping_insights(query, ranked or products, top3[0] if top3 else None)
    insights["total_matches"] = len(products)

    return {
        "summary": build_ai_summary(query, rankings, insights),
        "rankings": rankings,
        "insights": insights,
        "powered_by": "torch-intent",
    }


def _product_brief(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "title": p.get("product_title"),
        "marketplace": p.get("marketplace"),
        "price_pkr": p.get("price"),
        "relevance_percent": p.get("intent_relevance"),
        "value_score": p.get("shopper_value_score"),
        "url": p.get("product_url"),
    }


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
    except TypeError:
        response = model.generate_content(prompt)
    return (response.text or "").strip()


def _parse_gemini_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def rank_with_gemini(query: str, products: list[dict]) -> dict[str, Any]:
    matched = filter_products_for_query(_prefer_pk_products(products), query)
    if not matched:
        return {
            "summary": f"No products with '{query}' in the title were found on Pakistani stores.",
            "rankings": [],
            "insights": {},
            "powered_by": "none",
        }

    intent = analyze_query_intent(query)
    intent_ranked = rank_products_by_intent(matched, query, min_relevance=15.0)

    if not settings.gemini_api_key:
        return _smart_rankings(query, matched)

    try:
        import google.generativeai as genai  # noqa: F401
    except ImportError:
        return _smart_rankings(query, matched)

    # Send intent-sorted top products so Gemini sees mugs before measuring cups
    briefs = [_product_brief(p) for p in intent_ranked[:35]]
    intent_line = ""
    if intent.category_hint == "drinkware":
        intent_line = (
            'The user wants a DRINKING cup/mug (aesthetic drinkware), NOT a resin/measuring/DIY craft cup. '
            "Prefer titles with mug, coffee, tea, ceramic, glass, tumbler."
        )

    prompt = f"""You are TORCH, a shopping advisor for customers in Pakistan.

User searched for: "{query}"
{intent_line}

Products (PKR, sorted by relevance to shopper intent):
{json.dumps(briefs, ensure_ascii=False)}

Pick the BEST 3 product_id values from this list only. Never pick measuring cups, resin, or craft supplies for drinkware searches.

Return ONLY valid JSON:
{{
  "rankings": [
    {{"rank": 1, "product_id": "id", "reason": "one sentence why this fits the search intent"}},
    {{"rank": 2, "product_id": "id", "reason": "..."}},
    {{"rank": 3, "product_id": "id", "reason": "..."}}
  ]
}}
"""

    try:
        text = await asyncio.to_thread(_call_gemini, prompt)
        data = _parse_gemini_json(text)
        by_id = {str(p.get("id")): p for p in intent_ranked}
        rankings_out = []
        for r in data.get("rankings") or []:
            pid = str(r.get("product_id") or "")
            p = by_id.get(pid)
            if not p:
                continue
            if not title_matches_query(str(p.get("product_title") or ""), query):
                continue
            if float(p.get("intent_relevance") or 0) < 20:
                continue
            rankings_out.append(
                _ranking_from_product(
                    p,
                    int(r.get("rank") or len(rankings_out) + 1),
                    str(r.get("reason") or ""),
                )
            )
        if len(rankings_out) < 1:
            return _smart_rankings(query, matched)

        insights = build_shopping_insights(query, intent_ranked, rankings_out[0] if rankings_out else None)
        insights["total_matches"] = len(matched)
        return {
            "summary": build_ai_summary(query, rankings_out, insights),
            "rankings": rankings_out[:3],
            "insights": insights,
            "powered_by": "gemini",
        }
    except Exception as e:
        log.exception("gemini ranking failed: %s", e)
        return _smart_rankings(query, matched)
