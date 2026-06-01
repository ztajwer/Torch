from __future__ import annotations

from app.scrapers.http_client import Fetcher
from app.scrapers.sources.webscraperio_ecommerce import WebscraperIoEcommerceScraper


class WebscraperAjaxScraper(WebscraperIoEcommerceScraper):
    source_id = "webscraper.io/ajax"
    marketplace_name = "Webscraper Ajax"
    base_url = "https://webscraper.io/test-sites/e-commerce/ajax"
