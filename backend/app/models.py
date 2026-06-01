from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class Product(BaseModel):
    id: str
    product_title: str

    price: float = Field(ge=0)
    original_price: Optional[float] = Field(default=None, ge=0)

    rating: Optional[float] = Field(default=None, ge=0, le=5)
    review_count: Optional[int] = Field(default=None, ge=0)

    brand_or_seller: Optional[str] = None
    category: Optional[str] = None

    marketplace: str
    availability: Optional[str] = None

    product_url: HttpUrl
    image_url: Optional[HttpUrl] = None

    timestamp_scraped: datetime

    # Enrichment fields
    normalized_title: str
    dedupe_key: str
    trend_score: float = 0.0
    best_value_score: float = 0.0


class Marketplace(BaseModel):
    id: str
    name: str
    base_url: HttpUrl
    enabled: bool = True
    scraper: str


class AnalyticsBundle(BaseModel):
    generated_at: datetime
    totals: dict[str, int]
    kpis: dict[str, float]
    top_rated_products: list[str]
    lowest_price_products: list[str]
    most_reviewed_products: list[str]
    trending_products: list[str]
    best_value_products: list[str]
    marketplace_rankings: list[dict]
    category_distribution: list[dict]
    price_distribution: list[dict]


class RefreshResult(BaseModel):
    status: Literal["ok", "partial", "failed"]
    message: str
    sources_run: list[str]
    products_written: int
    analytics_written: bool

