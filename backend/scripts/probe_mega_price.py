import re

import httpx
from selectolax.parser import HTMLParser

html = httpx.get(
    "https://www.mega.pk/search/samsung/",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text
doc = HTMLParser(html)
for a in doc.css("a[href*='mobiles_products']"):
    title = (a.text() or "").strip()
    if "A07" not in title or len(title) < 10:
        continue
    href = a.attributes.get("href") or ""
    # walk up for price container
    node = a
    for _ in range(12):
        if node is None:
            break
        text = node.text(strip=True)
        prices = re.findall(r"([\d,]+)\s*-\s*PKR", text, flags=re.I)
        if prices:
            print("title:", title[:60])
            print("prices in node:", prices)
            print("node tag:", node.tag, "class:", node.attributes.get("class"))
            break
        node = node.parent
    break

# table top 10 section
m = re.search(
    r"Top 10 Search for .+?ProductsPrice(.{0,8000})",
    html,
    flags=re.I | re.S,
)
if m:
    block = m.group(1)
    for line in re.findall(r"Galaxy A07[^\n]{0,80}(\d[\d,]*)\s*-\s*Rs", block):
        print("top10:", line)
