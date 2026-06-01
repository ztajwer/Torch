from __future__ import annotations

import logging
import re
from typing import AsyncIterator, Optional
from urllib.parse import urljoin

from app.pipeline.search_match import title_matches_query

from selectolax.parser import HTMLParser

from app.scrapers.base import BaseScraper, RawProduct
from app.scrapers.http_client import Fetcher


log = logging.getLogger("torch.scrape.webscraperio")


def _to_float(s: str) -> Optional[float]:
    s = s.strip()
    s = re.sub(r"[^\d.]+", "", s)
    try:
        return float(s)
    except Exception:
        return None


def _to_int(s: str) -> Optional[int]:
    s = s.strip()
    s = re.sub(r"[^\d]+", "", s)
    try:
        return int(s)
    except Exception:
        return None


class WebscraperIoEcommerceScraper(BaseScraper):
    source_id = "webscraper.io/test-sites/e-commerce"
    marketplace_name = "WebscraperEcommerce"
    base_url = "https://webscraper.io/test-sites/e-commerce/allinone"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        # This test-site uses category navigation, pagination inside categories.
        root_html = await self.fetcher.get(self.base_url, referer="https://webscraper.io/")
        root = HTMLParser(root_html)
        categories = root.css("div.sidebar-nav a.category-link")
        cat_hrefs = [a.attributes.get("href") for a in categories if a.attributes.get("href")]
        if not cat_hrefs:
            # fallback selector
            categories = root.css("div.sidebar-nav a")
            cat_hrefs = [a.attributes.get("href") for a in categories if a.attributes.get("href")]

        cat_urls = []
        for href in cat_hrefs:
            if not href:
                continue
            if "product" in href:
                continue
            cat_urls.append(urljoin(self.base_url, href))

        seen_cat = set()
        for cat_url in cat_urls:
            if cat_url in seen_cat:
                continue
            seen_cat.add(cat_url)

            for page in range(1, max_pages + 1):
                page_url = cat_url if page == 1 else f"{cat_url}?page={page}"
                try:
                    html = await self.fetcher.get(page_url, referer=cat_url)
                except Exception as e:
                    log.warning("page fetch failed url=%s err=%s", page_url, type(e).__name__)
                    break

                doc = HTMLParser(html)
                cards = doc.css("div.thumbnail")
                if not cards:
                    break

                for c in cards:
                    title_el = c.css_first("a.title")
                    price_el = c.css_first("h4.price")
                    rating_el = c.css_first("div.ratings p[data-rating]")
                    reviews_el = c.css_first("div.ratings p.pull-right")
                    img_el = c.css_first("img")

                    title = (title_el.attributes.get("title") if title_el else None) or (title_el.text().strip() if title_el else "")
                    if query and not title_matches_query(title or "", query):
                        continue
                    href = title_el.attributes.get("href") if title_el else ""
                    product_url = urljoin(page_url, href) if href else page_url
                    price = _to_float(price_el.text()) if price_el else None

                    rating = None
                    if rating_el and rating_el.attributes.get("data-rating"):
                        rating = _to_float(rating_el.attributes["data-rating"])

                    review_count = _to_int(reviews_el.text()) if reviews_el else None
                    image_url = urljoin(page_url, img_el.attributes.get("src")) if img_el and img_el.attributes.get("src") else None

                    # Category label from breadcrumb-like nav if present
                    category = None
                    crumb = doc.css_first("ul.breadcrumb li.active")
                    if crumb:
                        category = crumb.text().strip() or None

                    yield RawProduct(
                        product_title=title or "Unknown",
                        price=price,
                        original_price=None,
                        rating=rating,
                        review_count=review_count,
                        brand_or_seller=None,
                        category=category,
                        marketplace=self.marketplace_name,
                        availability=None,
                        product_url=product_url,
                        image_url=image_url,
                        timestamp_scraped=self.now_utc(),
                    )

