from __future__ import annotations

import logging
import re
from typing import AsyncIterator, Optional
from urllib.parse import quote_plus, urljoin

from app.pipeline.search_match import is_tech_product_query, title_matches_query

from selectolax.parser import HTMLParser

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher


log = logging.getLogger("torch.scrape.books")


def _to_float(s: str) -> Optional[float]:
    s = s.strip()
    s = re.sub(r"[^\d.]+", "", s)
    try:
        return float(s)
    except Exception:
        return None


def _rating_to_float(cls: str) -> Optional[float]:
    m = {
        "One": 1.0,
        "Two": 2.0,
        "Three": 3.0,
        "Four": 4.0,
        "Five": 5.0,
    }
    for k, v in m.items():
        if k in cls:
            return v
    return None


class BooksToScrapeScraper(BaseScraper):
    source_id = "books.toscrape.com"
    marketplace_name = "BooksToScrape"
    base_url = "https://books.toscrape.com/"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        if query and is_tech_product_query(query):
            return
        if query:
            async for item in self._scrape_search(query=query, max_pages=max_pages):
                yield item
            return

        # Site uses catalog/page-X.html
        for page in range(1, max_pages + 1):
            page_url = urljoin(self.base_url, f"catalogue/page-{page}.html")
            try:
                html = await self.fetcher.get(page_url, referer=self.base_url)
            except Exception as e:
                log.warning("page fetch failed page=%s err=%s", page, type(e).__name__)
                continue

            doc = HTMLParser(html)
            items = doc.css("article.product_pod")
            if not items:
                break

            for it in items:
                a = it.css_first("h3 a")
                if not a:
                    continue
                title = (a.attributes.get("title") or "").strip() or (a.text() or "").strip()
                href = a.attributes.get("href") or ""
                product_url = urljoin(page_url, href)

                price_el = it.css_first(".price_color")
                price = _to_float(price_el.text()) if price_el else None

                rating_el = it.css_first(".star-rating")
                rating = _rating_to_float(" ".join(rating_el.attributes.get("class", "").split())) if rating_el else None

                img = it.css_first("img")
                image_url = urljoin(page_url, img.attributes.get("src")) if img and img.attributes.get("src") else None

                availability_el = it.css_first(".availability")
                availability = availability_el.text().strip() if availability_el else None

                yield self._raw(
                    title=title,
                    price=price,
                    rating=rating,
                    availability=availability,
                    product_url=product_url,
                    image_url=image_url,
                )

    async def _scrape_search(self, *, query: str, max_pages: int) -> AsyncIterator[RawProduct]:
        """Search via site form URL; fall back to catalog crawl + title filter."""
        q = quote_plus(query.strip())
        found = 0
        for page in range(1, max_pages + 1):
            page_url = urljoin(
                self.base_url,
                f"catalogue/search/?q={q}&page={page}" if page > 1 else f"catalogue/search/?q={q}",
            )
            try:
                html = await self.fetcher.get(page_url, referer=self.base_url)
            except Exception as e:
                log.warning("search fetch failed page=%s err=%s", page, type(e).__name__)
                break

            page_found = 0
            async for product in self._iter_listing(html, page_url, query=query):
                page_found += 1
                found += 1
                yield product
            if page_found == 0:
                break

        if found > 0:
            return

        log.info("books search empty/failed; falling back to catalog filter query=%s", query)
        for page in range(1, max_pages + 1):
            page_url = urljoin(self.base_url, f"catalogue/page-{page}.html")
            try:
                html = await self.fetcher.get(page_url, referer=self.base_url)
            except Exception as e:
                log.warning("catalog fallback failed page=%s err=%s", page, type(e).__name__)
                break
            page_found = 0
            async for product in self._iter_listing(html, page_url, query=query):
                page_found += 1
                yield product
            if page_found == 0 and page > 2:
                break

    async def _iter_listing(
        self, html: str, page_url: str, *, query: Optional[str] = None
    ) -> AsyncIterator[RawProduct]:
        doc = HTMLParser(html)
        for it in doc.css("article.product_pod"):
            a = it.css_first("h3 a")
            if not a:
                continue
            title = (a.attributes.get("title") or "").strip() or (a.text() or "").strip()
            if query and not title_matches_query(title, query):
                continue
            href = a.attributes.get("href") or ""
            product_url = urljoin(page_url, href)
            price_el = it.css_first(".price_color")
            price = _to_float(price_el.text()) if price_el else None
            rating_el = it.css_first(".star-rating")
            rating = _rating_to_float(" ".join(rating_el.attributes.get("class", "").split())) if rating_el else None
            img = it.css_first("img")
            image_url = urljoin(page_url, img.attributes.get("src")) if img and img.attributes.get("src") else None
            availability_el = it.css_first(".availability")
            availability = availability_el.text().strip() if availability_el else None
            yield self._raw(
                title=title,
                price=price,
                rating=rating,
                availability=availability,
                product_url=product_url,
                image_url=image_url,
            )

    def _raw(
        self,
        *,
        title: str,
        price: Optional[float],
        rating: Optional[float],
        availability: Optional[str],
        product_url: str,
        image_url: Optional[str],
    ) -> RawProduct:
        return RawProduct(
            product_title=title,
            price=price,
            original_price=None,
            rating=rating,
            review_count=None,
            brand_or_seller=None,
            category="Books",
            marketplace=self.marketplace_name,
            availability=availability,
            product_url=product_url,
            image_url=image_url,
            timestamp_scraped=self.now_utc(),
        )

