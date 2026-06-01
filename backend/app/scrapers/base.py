from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Optional


@dataclass(frozen=True)
class RawProduct:
    product_title: str
    price: Optional[float]
    original_price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    brand_or_seller: Optional[str]
    category: Optional[str]
    marketplace: str
    availability: Optional[str]
    product_url: str
    image_url: Optional[str]
    timestamp_scraped: datetime


class BaseScraper(ABC):
    source_id: str
    marketplace_name: str
    base_url: str

    @abstractmethod
    async def scrape(self, *, max_pages: int, query: Optional[str] = None) -> AsyncIterator[RawProduct]:
        raise NotImplementedError

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)

