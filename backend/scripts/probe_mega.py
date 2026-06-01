import asyncio

from selectolax.parser import HTMLParser

from app.scrapers.http_client import Fetcher


async def main() -> None:
    f = Fetcher(timeout_s=25, max_retries=2, rate_limit_rps=1)
    url = "https://www.mega.pk/search/iphone/"
    html = await f.get(url, referer="https://www.mega.pk/")
    doc = HTMLParser(html)
    print("len", len(html))
    title = doc.css_first("title")
    print("title", title.text()[:80] if title else "")
    for sel in [".search-result", "table tr", ".product", "a[href*='products']", ".cpt", "div.item"]:
        n = len(doc.css(sel))
        if n:
            print(sel, n)
    for a in doc.css("a[href]"):
        href = a.attributes.get("href") or ""
        if href.startswith("https://www.mega.pk/") and "javascript" not in href:
            t = (a.text() or "").strip()
            if len(t) > 15 and "PKR" not in t:
                print("link", href[:100], "|", t[:60])
                if len([x for x in doc.css("a[href]") if (x.attributes.get("href") or "").startswith("https://www.mega.pk/")]) > 5:
                    pass
    # price patterns
    import re

    for m in re.finditer(r"([\d,]+)\s*-\s*PKR", html[:50000]):
        print("price", m.group(0))
        break
    tr = doc.css("table tr")
    print("tr count", len(tr))
    for i, row in enumerate(tr[1:6], 1):
        print(f"--- row {i} ---")
        print(row.text(strip=True)[:200])
        for a in row.css("a[href]"):
            print("  a", a.attributes.get("href"), (a.text() or "")[:50])


if __name__ == "__main__":
    asyncio.run(main())
