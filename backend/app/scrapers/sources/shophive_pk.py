from __future__ import annotations

import logging
from typing import AsyncIterator, Optional
from urllib.parse import quote_plus, urljoin

from selectolax.parser import HTMLParser

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher
from app.scrapers.sources.pk_utils import first_img, parse_pkr_price, sanitize_pkr_price


log = logging.getLogger("torch.scrape.shophive")


class ShophivePkScraper(BaseScraper):
    source_id = "shophive.com"
    marketplace_name = "Shophive Pakistan"
    base_url = "https://www.shophive.com/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if not query:
            return
        url = f"{self.base_url}catalogsearch/result/?q={quote_plus(query.strip())}"
        try:
            html = await self.fetcher.get(url, referer=self.base_url)
        except Exception as e:
            log.warning("shophive search failed err=%s", type(e).__name__)
            return

        doc = HTMLParser(html)
        for it in doc.css("li.product-item") or doc.css(".product-item-info"):
            link = it.css_first("a.product-item-link") or it.css_first("a[href*='.html']")
            if not link:
                continue
            title = (link.attributes.get("title") or link.text() or "").strip()
            if not title or len(title) < 4:
                continue
            href = link.attributes.get("href") or ""
            product_url = urljoin(self.base_url, href)
            price_el = it.css_first("[data-price-type='finalPrice']") or it.css_first(".price")
            price = sanitize_pkr_price(parse_pkr_price(price_el.text() if price_el else it.text()), title)
            yield RawProduct(
                product_title=title,
                price=price,
                original_price=None,
                rating=None,
                review_count=None,
                brand_or_seller=None,
                category="Electronics",
                marketplace=self.marketplace_name,
                availability=None,
                product_url=product_url,
                image_url=first_img(it, self.base_url),
                timestamp_scraped=self.now_utc(),
            )
