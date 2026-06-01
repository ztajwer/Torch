from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Optional
from urllib.parse import quote_plus, urljoin

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher
from app.scrapers.sources.pk_utils import parse_pkr_price, sanitize_pkr_price


log = logging.getLogger("torch.scrape.daraz")


def _daraz_url(path: str) -> str:
    if path.startswith("http"):
        return path
    if path.startswith("//"):
        return "https:" + path
    return urljoin("https://www.daraz.pk/", path.lstrip("/"))


class DarazPkScraper(BaseScraper):
    """Real-time search via Daraz catalog JSON API (?ajax=true)."""

    source_id = "daraz.pk"
    marketplace_name = "Daraz Pakistan"
    base_url = "https://www.daraz.pk/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def _items_from_payload(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        mods = data.get("mods") or data.get("data", {}).get("mods") or {}
        items = mods.get("listItems") or []
        return items if isinstance(items, list) else []

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if not query:
            return
        q = quote_plus(query.strip())
        pages = max(1, min(max_pages, 3))

        for page in range(1, pages + 1):
            url = f"{self.base_url}catalog/?ajax=true&q={q}&page={page}&_keyori=ss"
            try:
                data = await self.fetcher.get_json(
                    url,
                    referer=f"{self.base_url}catalog/?q={q}",
                    accept="application/json",
                )
            except Exception as e:
                log.warning("daraz search failed page=%s err=%s", page, type(e).__name__)
                break

            if not isinstance(data, dict):
                break
            items = self._items_from_payload(data)
            if not items:
                break

            for it in items:
                title = (it.get("name") or "").strip()
                if not title or len(title) < 3:
                    continue
                price = sanitize_pkr_price(
                    parse_pkr_price(str(it.get("priceShow") or it.get("originalPriceShow") or "")),
                    title,
                )
                if price is None:
                    continue
                item_url = _daraz_url(str(it.get("itemUrl") or ""))
                rating_raw = it.get("ratingScore")
                rating = float(rating_raw) if rating_raw not in (None, "") else None
                reviews_raw = it.get("review")
                review_count = int(reviews_raw) if str(reviews_raw or "").isdigit() else None
                image = it.get("image")
                image_url = str(image) if image else None

                yield RawProduct(
                    product_title=title,
                    price=price,
                    original_price=parse_pkr_price(str(it.get("originalPriceShow") or "")),
                    rating=rating,
                    review_count=review_count,
                    brand_or_seller=it.get("brandName"),
                    category="General",
                    marketplace=self.marketplace_name,
                    availability="In stock" if it.get("inStock") else "Out of stock",
                    product_url=item_url,
                    image_url=image_url,
                    timestamp_scraped=self.now_utc(),
                )
