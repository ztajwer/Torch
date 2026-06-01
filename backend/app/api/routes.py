from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from app.ai.product_chat import product_chat_reply
from app.analytics.recommendations import compare_best
from app.api.utils import apply_filters, apply_sort, paginate
from app.pipeline.orchestrator import PipelineOrchestrator
from app.scrapers.registry import default_marketplaces
from app.storage.json_store import JsonStore


log = logging.getLogger("torch.api")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=120)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)
    context_query: Optional[str] = None


def build_router(store: JsonStore) -> APIRouter:
    router = APIRouter(prefix="/api")
    pipeline = PipelineOrchestrator(store)

    @router.get("/products")
    def get_products(
        q: Optional[str] = None,
        category: Optional[str] = None,
        marketplace: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        rating_min: Optional[float] = None,
        rating_max: Optional[float] = None,
        sort: str = "trend_desc",
        offset: int = 0,
        limit: int = 50,
    ):
        products = store.read_products()
        products = apply_filters(
            products,
            q=q,
            category=category,
            marketplace=marketplace,
            price_min=price_min,
            price_max=price_max,
            rating_min=rating_min,
            rating_max=rating_max,
        )
        products = apply_sort(products, sort)
        return paginate(products, offset=offset, limit=limit)

    @router.get("/products/{product_id}")
    def get_product(product_id: str):
        products = store.read_products()
        for p in products:
            if str(p.get("id")) == product_id:
                return p
        raise HTTPException(status_code=404, detail="Product not found")

    @router.get("/search")
    def search_products(
        q: str = Query(..., min_length=1),
        offset: int = 0,
        limit: int = 50,
    ):
        products = store.read_products()
        products = apply_filters(products, q=q)
        products = apply_sort(products, "trend_desc")
        return paginate(products, offset=offset, limit=limit)

    @router.get("/status")
    def status():
        products = store.read_products()
        return {
            "products": len(products),
            "stores": len(store.read_marketplaces() or default_marketplaces()),
            "ready": len(products) > 0,
        }

    @router.get("/filter")
    def filter_meta():
        products = store.read_products()
        categories = sorted({(p.get("category") or "Uncategorized") for p in products})
        marketplaces = sorted({(p.get("marketplace") or "Unknown") for p in products})
        return {"categories": categories, "marketplaces": marketplaces}

    @router.get("/compare")
    def compare(
        ids: Optional[str] = Query(None, description="Comma-separated product ids"),
        q: Optional[str] = Query(None, description="Product name search — compares all matches"),
    ):
        products = store.read_products()

        if q and q.strip():
            items = apply_filters(products, q=q.strip())
            items, best_id = compare_best(items)
            return {
                "items": items,
                "best_id": best_id,
                "query": q.strip(),
                "message": None if items else f"No products found matching '{q.strip()}'. Run Smart Search first.",
            }

        wanted = [x.strip() for x in (ids or "").split(",") if x.strip()]
        if not wanted:
            raise HTTPException(status_code=400, detail="Provide product ids or a search query (q).")

        by_id = {str(p.get("id")): p for p in products}
        items = [by_id[i] for i in wanted if i in by_id]
        items, best_id = compare_best(items)
        return {
            "items": items,
            "best_id": best_id,
            "message": None if items else "No products found for ids. Use Smart Search or pick from product list.",
        }

    @router.get("/intelligence/quick")
    async def intelligence_quick(q: str = Query(..., min_length=2, max_length=120)):
        """Instant results from fast stores + saved data (1–3 seconds)."""
        try:
            result = await pipeline.run_quick_search(q)
        except Exception as e:
            log.exception("quick search failed")
            raise HTTPException(status_code=500, detail=f"Search failed: {e}") from e
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Invalid query"))
        return result

    @router.post("/intelligence/search")
    async def intelligence_search(body: SearchRequest):
        """Scrape all stores in parallel and return best picks."""
        try:
            result = await pipeline.run_search_pipeline(body.query)
        except Exception as e:
            log.exception("intelligence search failed")
            raise HTTPException(status_code=500, detail=f"Search failed: {e}") from e
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Invalid query"))
        return result

    @router.get("/intelligence/search")
    async def intelligence_search_get(q: str = Query(..., min_length=2, max_length=120)):
        try:
            result = await pipeline.run_search_pipeline(q)
        except Exception as e:
            log.exception("intelligence search failed")
            raise HTTPException(status_code=500, detail=f"Search failed: {e}") from e
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Invalid query"))
        return result

    @router.get("/analytics")
    def get_analytics():
        return store.read_analytics()

    @router.post("/chat")
    async def chat(body: ChatRequest):
        """Product-only shopping assistant (Gemini + catalog context)."""
        try:
            result = await product_chat_reply(
                message=body.message,
                history=[m.model_dump() for m in body.history],
                products=store.read_products(),
                context_query=body.context_query,
            )
        except Exception as e:
            log.exception("chat endpoint failed")
            raise HTTPException(status_code=500, detail=f"Chat failed: {e}") from e
        return result

    async def _run_pipeline_bg():
        try:
            await pipeline.run_full_pipeline()
        except Exception:
            log.exception("background refresh failed")

    @router.post("/refresh")
    async def refresh(background_tasks: BackgroundTasks):
        # Fire-and-forget refresh; UI keeps working with old data.
        background_tasks.add_task(_run_pipeline_bg)
        return {"status": "started"}

    @router.get("/logs")
    def get_logs(limit: int = 200):
        items = store.read_logs()
        return {"items": items[-min(max(int(limit), 1), 2000) :]}

    return router

