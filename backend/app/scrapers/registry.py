from __future__ import annotations

from app.scrapers.http_client import Fetcher
from app.scrapers.sources.daraz_pk import DarazPkScraper
from app.scrapers.sources.mega_pk import MegaPkScraper
from app.scrapers.sources.priceoye_pk import PriceOyePkScraper
from app.scrapers.sources.shophive_pk import ShophivePkScraper
from app.scrapers.sources.telemart_pk import TelemartPkScraper

# Substrings matched against product.marketplace when filtering search results.
PK_MARKETPLACE_HINTS: tuple[str, ...] = (
    "PriceOye",
    "Daraz",
    "Telemart",
    "Shophive",
    "Mega.pk",
)


def is_pk_marketplace(name: str | None) -> bool:
    n = name or ""
    return any(h in n for h in PK_MARKETPLACE_HINTS)


def build_scrapers(fetcher: Fetcher):
    """Pakistani e-commerce stores only."""
    return [
        PriceOyePkScraper(fetcher),
        DarazPkScraper(fetcher),
        TelemartPkScraper(fetcher),
        MegaPkScraper(fetcher),
        ShophivePkScraper(fetcher),
    ]


def build_fast_scrapers(fetcher: Fetcher):
    return [PriceOyePkScraper(fetcher), DarazPkScraper(fetcher), MegaPkScraper(fetcher)]


def default_marketplaces() -> list[dict]:
    return [
        {"id": "priceoye", "name": "PriceOye", "base_url": "https://priceoye.pk/", "enabled": True},
        {"id": "daraz", "name": "Daraz Pakistan", "base_url": "https://www.daraz.pk/", "enabled": True},
        {"id": "telemart", "name": "Telemart", "base_url": "https://www.telemart.pk/", "enabled": True},
        {"id": "mega", "name": "Mega.pk", "base_url": "https://www.mega.pk/", "enabled": True},
        {"id": "shophive", "name": "Shophive", "base_url": "https://www.shophive.com/", "enabled": True},
    ]


def store_count() -> int:
    return len(default_marketplaces())
