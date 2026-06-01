from __future__ import annotations

import logging
from typing import AsyncIterator, Optional
from app.pipeline.search_match import title_matches_query
from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher


log = logging.getLogger("torch.scrape.fakestore")


class FakeStoreApiScraper(BaseScraper):
    source_id = "fakestoreapi.com"
    marketplace_name = "FakeStore"
    base_url = "https://fakestoreapi.com/products"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        try:
            data = await self.fetcher.get_json(self.base_url)
        except Exception as e:
            log.warning("fakestore fetch failed err=%s", type(e).__name__)
            return
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            if query and not title_matches_query(title, query):
                continue
            price = item.get("price")
            rating = item.get("rating", {})
            rate_val = rating.get("rate") if isinstance(rating, dict) else rating
            count_val = rating.get("count") if isinstance(rating, dict) else None
            pid = item.get("id")
            product_url = f"https://fakestoreapi.com/products/{pid}"
            yield RawProduct(
                product_title=title,
                price=float(price) if price is not None else None,
                original_price=None,
                rating=float(rate_val) if rate_val is not None else None,
                review_count=int(count_val) if count_val is not None else None,
                brand_or_seller=None,
                category=str(item.get("category") or "General"),
                marketplace=self.marketplace_name,
                availability="In stock",
                product_url=product_url,
                image_url=str(item.get("image") or "") or None,
                timestamp_scraped=self.now_utc(),
            )
