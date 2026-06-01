from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Optional

import httpx


log = logging.getLogger("torch.scrape.http")


DEFAULT_UAS = [
    # Small rotation to reduce trivial blocking.
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


@dataclass
class Fetcher:
    timeout_s: float
    max_retries: int
    rate_limit_rps: float
    user_agents: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.user_agents is None:
            self.user_agents = DEFAULT_UAS[:]
        self._min_delay = 1.0 / max(self.rate_limit_rps, 0.1)
        self._lock = asyncio.Lock()
        self._last_ts: float = 0.0

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait = (self._last_ts + self._min_delay) - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_ts = asyncio.get_event_loop().time()

    async def get(self, url: str, *, referer: Optional[str] = None) -> str:
        await self._rate_limit()
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if referer:
            headers["Referer"] = referer

        attempt = 0
        last_err: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=True) as client:
            while attempt < self.max_retries:
                attempt += 1
                try:
                    r = await client.get(url, headers=headers)
                    if r.status_code in (429, 503, 502, 500):
                        backoff = min(8.0, 0.6 * (2 ** (attempt - 1))) + random.random() * 0.2
                        log.warning("retryable status=%s url=%s backoff=%.2fs", r.status_code, url, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    r.raise_for_status()
                    return r.text
                except Exception as e:
                    last_err = e
                    backoff = min(8.0, 0.6 * (2 ** (attempt - 1))) + random.random() * 0.2
                    log.warning("fetch failed attempt=%s url=%s err=%s backoff=%.2fs", attempt, url, type(e).__name__, backoff)
                    await asyncio.sleep(backoff)

        raise RuntimeError(f"Failed to fetch {url}: {last_err}")

    async def get_json(
        self,
        url: str,
        *,
        referer: Optional[str] = None,
        accept: str = "application/json",
    ) -> object:
        await self._rate_limit()
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": accept,
            "Accept-Language": "en-PK,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        }
        if referer:
            headers["Referer"] = referer
        async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()

