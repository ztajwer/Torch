from __future__ import annotations

import logging
import re
from typing import AsyncIterator, Optional
from urllib.parse import quote, urljoin

from selectolax.parser import HTMLParser

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher
from app.scrapers.sources.pk_utils import first_img, price_from_mega_node, sanitize_pkr_price


log = logging.getLogger("torch.scrape.mega")

_PRODUCT_PATH = re.compile(r"_products/\d+/", re.I)


class MegaPkScraper(BaseScraper):
    source_id = "mega.pk"
    marketplace_name = "Mega.pk"
    base_url = "https://www.mega.pk/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def _search_url(self, query: str) -> str:
        slug = re.sub(r"\s+", "-", query.strip().lower())
        slug = quote(slug, safe="-")
        return f"{self.base_url}search/{slug}/"

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if not query:
            return
        url = self._search_url(query)
        try:
            html = await self.fetcher.get(url, referer=self.base_url)
        except Exception as e:
            log.warning("mega.pk search failed err=%s", type(e).__name__)
            return

        doc = HTMLParser(html)
        seen_urls: set[str] = set()

        for a in doc.css("a[href]"):
            href = a.attributes.get("href") or ""
            if not _PRODUCT_PATH.search(href):
                continue
            product_url = urljoin(self.base_url, href)
            if product_url in seen_urls:
                continue
            title = (a.text() or "").strip()
            if not title or len(title) < 6:
                continue
            seen_urls.add(product_url)

            price = price_from_mega_node(a)
            if price is None:
                continue

            category = "Mobiles"
            if "laptop" in href.lower():
                category = "Laptops"
            elif "tablet" in href.lower():
                category = "Tablets"

            yield RawProduct(
                product_title=title,
                price=price,
                original_price=None,
                rating=None,
                review_count=None,
                brand_or_seller=None,
                category=category,
                marketplace=self.marketplace_name,
                availability="In stock",
                product_url=product_url,
                image_url=first_img(a, self.base_url),
                timestamp_scraped=self.now_utc(),
            )
