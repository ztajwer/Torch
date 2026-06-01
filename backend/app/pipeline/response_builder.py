from __future__ import annotations

from typing import Any

from app.analytics.recommendations import (
    compare_best,
    group_by_marketplace,
    pick_recommendations,
    valid_priced_products,
)
from app.ai.gemini_advisor import rank_with_gemini


async def build_search_response(
    *,
    query: str,
    matches: list[dict],
    sources_scraped: list[str],
    scraped_count: int,
    phase: str = "complete",
    store_count: int = 0,
) -> dict[str, Any]:
    from app.pipeline.query_intent import filter_for_display

    priced_matches = valid_priced_products(matches)
    priced_matches = filter_for_display(priced_matches, query) if query else priced_matches
    compare_items, best_id = compare_best(priced_matches)
    recommendations = pick_recommendations(priced_matches, query=query)
    marketplaces = group_by_marketplace(priced_matches)

    ai = await rank_with_gemini(query, priced_matches)
    if ai.get("rankings"):
        best_id = str(ai["rankings"][0].get("product_id") or best_id or "")

    user_message = None
    if not priced_matches:
        user_message = (
            f"No products with '{query}' in the title on Pakistani stores. Try a different spelling or product name."
        )

    return {
        "status": "ok",
        "phase": phase,
        "query": query,
        "store_count": store_count or len(marketplaces),
        "sources_scraped": sources_scraped,
        "scraped_count": scraped_count,
        "total_matches": len(priced_matches),
        "user_message": user_message,
        "items": priced_matches[:200],
        "compare": {"items": compare_items, "best_id": best_id},
        "by_marketplace": marketplaces,
        "recommendations": recommendations,
        "ai": ai,
    }
