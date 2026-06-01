"""Probe PK store search HTML for scraper selectors."""
import asyncio
import re

import httpx
from selectolax.parser import HTMLParser


async def probe(name: str, url: str) -> None:
    print(f"\n=== {name} ===")
    try:
        r = httpx.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
                "Accept-Language": "en-PK,en;q=0.9",
            },
            timeout=30,
            follow_redirects=True,
        )
        print("status", r.status_code, "len", len(r.text))
        doc = HTMLParser(r.text)
        for sel in [
            ".productBox",
            ".product-item",
            ".product-card",
            "[class*='product']",
            "div[data-qa-locator='product-item']",
            ".gridItem",
            "a[href*='product']",
            "a[href*='_products']",
        ]:
            n = len(doc.css(sel))
            if n:
                print(f"  {sel}: {n}")
        # sample product titles
        for a in doc.css("a[href]")[:200]:
            href = a.attributes.get("href") or ""
            t = (a.text() or "").strip()
            if len(t) > 10 and len(t) < 120 and "http" not in t.lower():
                if any(
                    x in href.lower()
                    for x in ("product", "mobile", "laptop", "item", ".html", "/p/")
                ):
                    print("  sample:", t[:70], "|", href[:80])
                    break
    except Exception as e:
        print("ERR", type(e).__name__, e)


async def main() -> None:
    stores = [
        ("priceoye", "https://priceoye.pk/search?q=iphone"),
        ("telemart", "https://www.telemart.pk/search?q=iphone"),
        ("telemart2", "https://www.telemart.pk/catalogsearch/result/?q=iphone"),
        ("daraz", "https://www.daraz.pk/catalog/?q=iphone"),
        ("mega", "https://www.mega.pk/search/iphone/"),
        ("shophive", "https://www.shophive.com/catalogsearch/result/?q=iphone"),
        ("ludo-daraz", "https://www.daraz.pk/catalog/?q=ludo"),
        ("ludo-mega", "https://www.mega.pk/search/ludo/"),
    ]
    for name, url in stores:
        await probe(name, url)


if __name__ == "__main__":
    asyncio.run(main())
