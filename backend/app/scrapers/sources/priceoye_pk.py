from __future__ import annotations

import logging
from typing import AsyncIterator, Optional
from urllib.parse import quote_plus, urljoin

from selectolax.parser import HTMLParser

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher
from app.scrapers.sources.pk_utils import first_img, parse_pkr_price, sanitize_pkr_price


log = logging.getLogger("torch.scrape.priceoye")


class PriceOyePkScraper(BaseScraper):
    source_id = "priceoye.pk"
    marketplace_name = "PriceOye Pakistan"
    base_url = "https://priceoye.pk/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if not query:
            return
        url = f"{self.base_url}search?q={quote_plus(query.strip())}"
        try:
            html = await self.fetcher.get(url, referer=self.base_url)
        except Exception as e:
            log.warning("priceoye search failed err=%s", type(e).__name__)
            return

        doc = HTMLParser(html)
        for box in doc.css(".productBox"):
            card = box.css_first("a.product-card")
            if not card:
                continue
            title = (card.attributes.get("data-product-name") or card.text() or "").strip()
            if not title:
                continue
            href = card.attributes.get("href") or ""
            product_url = urljoin(self.base_url, href)
            price_el = box.css_first(".price-box") or box.css_first("[class*='price']")
            price = sanitize_pkr_price(parse_pkr_price(price_el.text() if price_el else ""), title)
            image_url = first_img(box, self.base_url)
            yield RawProduct(
                product_title=title,
                price=price,
                original_price=None,
                rating=None,
                review_count=None,
                brand_or_seller=box.attributes.get("data-brand"),
                category="Mobiles & Electronics",
                marketplace=self.marketplace_name,
                availability="In stock",
                product_url=product_url,
                image_url=image_url,
                timestamp_scraped=self.now_utc(),
            )
