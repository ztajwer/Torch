from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.analytics.engine import build_analytics
from app.api.utils import apply_filters
from app.config import settings
from app.pipeline.normalize import deduplicate, to_unified_product
from app.pipeline.query_intent import (
    expand_search_queries,
    filter_for_display,
    product_matches_pipeline,
)
from app.pipeline.search_match import filter_products_for_query
from app.pipeline.response_builder import build_search_response
from app.scrapers.base import BaseScraper
from app.scrapers.http_client import Fetcher
from app.scrapers.registry import (
    build_fast_scrapers,
    build_scrapers,
    default_marketplaces,
    is_pk_marketplace,
    store_count,
)
from app.storage.json_store import JsonStore


log = logging.getLogger("torch.pipeline")


class PipelineOrchestrator:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.fetcher = Fetcher(
            timeout_s=settings.search_timeout_s,
            max_retries=settings.max_retries,
            rate_limit_rps=settings.rate_limit_rps,
        )
        self.fast_fetcher = Fetcher(
            timeout_s=settings.search_timeout_s,
            max_retries=2,
            rate_limit_rps=settings.search_rate_limit_rps,
        )

    async def _collect_scraper(self, scraper: BaseScraper, *, query: str | None, max_pages: int) -> tuple[str, list[dict]]:
        items: list[dict] = []
        try:
            async for raw in scraper.scrape(max_pages=max_pages, query=query):
                items.append(to_unified_product(raw))
        except Exception:
            log.exception("scraper failed source=%s", scraper.source_id)
            raise
        return scraper.marketplace_name, items

    def _pk_only_matches(self, matches: list[dict]) -> list[dict]:
        pk = [m for m in matches if is_pk_marketplace(m.get("marketplace"))]
        return pk

    def _scrapers_for_query(self, scrapers: list[BaseScraper], query: str | None) -> list[BaseScraper]:
        return scrapers

    async def _parallel_scrape(
        self, scrapers: list[BaseScraper], *, query: str | None, max_pages: int
    ) -> tuple[list[str], list[dict]]:
        scrapers = self._scrapers_for_query(scrapers, query)
        if not scrapers:
            return [], []

        async def safe_collect(s: BaseScraper) -> tuple[str, list[dict]]:
            try:
                return await self._collect_scraper(s, query=query, max_pages=max_pages)
            except Exception:
                return s.marketplace_name, []

        results = await asyncio.gather(*[safe_collect(s) for s in scrapers])
        sources_run: list[str] = []
        scraped: list[dict] = []
        for marketplace, items in results:
            if items:
                sources_run.append(marketplace)
                scraped.extend(items)
        return sources_run, scraped

    def _finalize_store(self, matches_query: str | None = None) -> list[dict]:
        all_products = self.store.read_products()
        analytics = build_analytics(all_products)
        self.store.write_products(all_products)
        self.store.write_analytics(analytics)
        if matches_query:
            matches = apply_filters(all_products, q=matches_query)
            return matches
        return all_products

    async def run_full_pipeline(self) -> dict[str, Any]:
        started = datetime.now(timezone.utc).isoformat()

        if not self.store.read_marketplaces():
            self.store.write_marketplaces(default_marketplaces())

        scrapers = build_scrapers(self.fetcher)
        sources_run, scraped = await self._parallel_scrape(
            scrapers, query=None, max_pages=settings.max_pages_per_source
        )

        unified = deduplicate(scraped)
        products_written = self.store.upsert_products(unified, key_field="id")
        self._finalize_store()

        self.store.append_log_event(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "info",
                "event": "pipeline_completed",
                "started": started,
                "sources_run": sources_run,
                "scraped_products": len(unified),
                "products_written": products_written,
            }
        )

        return {
            "status": "ok" if sources_run else "failed",
            "message": "Pipeline completed" if sources_run else "No scrapers executed",
            "sources_run": sources_run,
            "products_written": products_written,
            "analytics_written": True,
        }

    async def run_quick_search(self, query: str) -> dict[str, Any]:
        q = (query or "").strip()
        if len(q) < 2:
            return {"status": "error", "message": "Type at least 2 letters.", "query": q}

        cached = apply_filters(self.store.read_products(), q=q)
        fast_scrapers = build_fast_scrapers(self.fast_fetcher)
        sources, scraped = await self._parallel_scrape(fast_scrapers, query=q, max_pages=1)
        unified = deduplicate(scraped)
        unified = [u for u in unified if title_matches_query(u.get("product_title", ""), q)]
        if unified:
            self.store.upsert_products(unified, key_field="id")

        matches = filter_products_for_query(self._pk_only_matches(self._finalize_store(q)), q)

        return await build_search_response(
            query=q,
            matches=matches,
            sources_scraped=sources,
            scraped_count=len(unified),
            phase="quick",
            store_count=store_count(),
        )

    async def run_search_pipeline(self, query: str) -> dict[str, Any]:
        started = datetime.now(timezone.utc).isoformat()
        q = (query or "").strip()
        if len(q) < 2:
            return {"status": "error", "message": "Type at least 2 letters.", "query": q}

        if not self.store.read_marketplaces():
            self.store.write_marketplaces(default_marketplaces())

        scrapers = build_scrapers(self.fetcher)
        search_queries = expand_search_queries(q)
        sources_run: list[str] = []
        scraped: list[dict] = []
        for sq in search_queries:
            src, batch = await self._parallel_scrape(
                scrapers, query=sq, max_pages=settings.max_pages_per_search
            )
            for s in src:
                if s not in sources_run:
                    sources_run.append(s)
            scraped.extend(batch)

        unified = deduplicate(scraped)
        unified = [
            u
            for u in unified
            if product_matches_pipeline(str(u.get("product_title") or ""), q, expanded_queries=search_queries)
        ]
        self.store.upsert_products(unified, key_field="id")
        self._finalize_store()
        pk_catalog = self._pk_only_matches(self.store.read_products())
        seen_ids: set[str] = set()
        merged: list[dict] = []
        for p in pk_catalog:
            title = str(p.get("product_title") or "")
            if not product_matches_pipeline(title, q, expanded_queries=search_queries):
                continue
            pid = str(p.get("id") or "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                merged.append(p)

        matches = filter_for_display(merged, q)

        self.store.append_log_event(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "info",
                "event": "search_completed",
                "query": q,
                "started": started,
                "sources_run": sources_run,
                "scraped_products": len(unified),
                "matches": len(matches),
            }
        )

        return await build_search_response(
            query=q,
            matches=matches,
            sources_scraped=sources_run,
            scraped_count=len(unified),
            phase="complete",
            store_count=store_count(),
        )


def run_full_pipeline_sync(store: JsonStore) -> dict[str, Any]:
    return asyncio.run(PipelineOrchestrator(store).run_full_pipeline())


def run_search_pipeline_sync(store: JsonStore, query: str) -> dict[str, Any]:
    return asyncio.run(PipelineOrchestrator(store).run_search_pipeline(query))
