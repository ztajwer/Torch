from __future__ import annotations

import logging
from typing import AsyncIterator, Optional
from urllib.parse import quote_plus

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher


log = logging.getLogger("torch.scrape.dummyjson")


class DummyJsonApiScraper(BaseScraper):
    source_id = "dummyjson.com"
    marketplace_name = "DummyJSON Shop"
    base_url = "https://dummyjson.com/products"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        url = f"{self.base_url}/search?q={quote_plus((query or '').strip())}&limit=30" if query else f"{self.base_url}?limit=30"
        try:
            data = await self.fetcher.get_json(url)
        except Exception as e:
            log.warning("dummyjson fetch failed err=%s", type(e).__name__)
            return
        if not isinstance(data, dict):
            return
        products = data.get("products")
        if not isinstance(products, list):
            return
        for item in products:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            pid = item.get("id")
            product_url = f"https://dummyjson.com/products/{pid}"
            yield RawProduct(
                product_title=title,
                price=float(item.get("price")) if item.get("price") is not None else None,
                original_price=None,
                rating=float(item.get("rating")) if item.get("rating") is not None else None,
                review_count=int(item.get("stock") or 0) or None,
                brand_or_seller=str(item.get("brand") or "") or None,
                category=str(item.get("category") or "General"),
                marketplace=self.marketplace_name,
                availability="In stock",
                product_url=product_url,
                image_url=str(item.get("thumbnail") or "") or None,
                timestamp_scraped=self.now_utc(),
            )
