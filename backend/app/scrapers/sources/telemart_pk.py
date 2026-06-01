from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Optional
from urllib.parse import quote_plus

import httpx

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.sources.pk_utils import sanitize_pkr_price
from app.scrapers.http_client import Fetcher


log = logging.getLogger("torch.scrape.telemart")

_ALGOLIA_APP = "7Z6UNQYQER"
_ALGOLIA_KEY = "9b4c33f99e845fe1363fd4c6ceb0f467"
_ALGOLIA_INDEX = "products"


class TelemartPkScraper(BaseScraper):
    """Real-time search via Telemart's public Algolia index."""

    source_id = "telemart.pk"
    marketplace_name = "Telemart Pakistan"
    base_url = "https://www.telemart.pk/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def _algolia_search(self, query: str, *, hits_per_page: int) -> list[dict[str, Any]]:
        url = f"https://{_ALGOLIA_APP}-dsn.algolia.net/1/indexes/*/queries"
        headers = {
            "X-Algolia-Application-Id": _ALGOLIA_APP,
            "X-Algolia-API-Key": _ALGOLIA_KEY,
            "Content-Type": "application/json",
        }
        params = f"query={quote_plus(query)}&hitsPerPage={hits_per_page}"
        body = {"requests": [{"indexName": _ALGOLIA_INDEX, "params": params}]}
        await self.fetcher._rate_limit()
        async with httpx.AsyncClient(timeout=self.fetcher.timeout_s) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        results = data.get("results") or []
        if not results:
            return []
        hits = results[0].get("hits") or []
        return hits if isinstance(hits, list) else []

    @staticmethod
    def _price(hit: dict[str, Any]) -> float | None:
        for key in ("sale_price", "discounted_price", "price"):
            val = hit.get(key)
            if val is not None:
                try:
                    p = float(val)
                    if p > 0:
                        return p
                except (TypeError, ValueError):
                    continue
        return None

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if not query:
            return
        hits_per_page = min(40, max(20, max_pages * 12))
        try:
            hits = await self._algolia_search(query.strip(), hits_per_page=hits_per_page)
        except Exception as e:
            log.warning("telemart algolia failed err=%s", type(e).__name__)
            return

        for hit in hits:
            title = (hit.get("title") or "").strip()
            slug = (hit.get("slug") or "").strip()
            if not title or not slug:
                continue
            product_url = f"{self.base_url}{slug}"
            price = sanitize_pkr_price(self._price(hit), title)
            if price is None:
                continue
            rating_raw = hit.get("rating")
            rating = float(rating_raw) if rating_raw not in (None, "") else None
            reviews = hit.get("reviewsCount")
            review_count = int(reviews) if str(reviews or "").isdigit() else None

            yield RawProduct(
                product_title=title,
                price=price,
                original_price=float(hit["price"]) if hit.get("price") and price else None,
                rating=rating,
                review_count=review_count,
                brand_or_seller=hit.get("brand"),
                category="Electronics",
                marketplace=self.marketplace_name,
                availability="In stock" if int(hit.get("qty") or 0) > 0 else None,
                product_url=product_url,
                image_url=hit.get("mainImageLink") or hit.get("placeholder_link"),
                timestamp_scraped=self.now_utc(),
            )
