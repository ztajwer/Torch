from __future__ import annotations

from app.scrapers.http_client import Fetcher
from app.scrapers.sources.webscraperio_ecommerce import WebscraperIoEcommerceScraper


class WebscraperStaticScraper(WebscraperIoEcommerceScraper):
    source_id = "webscraper.io/static"
    marketplace_name = "Webscraper Static"
    base_url = "https://webscraper.io/test-sites/e-commerce/static"
