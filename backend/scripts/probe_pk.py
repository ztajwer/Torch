import re
import httpx
from selectolax.parser import HTMLParser

h = httpx.get(
    "https://priceoye.pk/search?q=iphone",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=25,
).text
doc = HTMLParser(h)
box = doc.css(".productBox")[0]
print(box.text()[:300])
for sel in [".price", ".price-box", ".p-price", "[class*='price']"]:
    p = box.css(sel)
    if p:
        print(sel, p[0].text())
