import re

import httpx

r = httpx.get(
    "https://www.telemart.pk/search?q=iphone",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"},
    timeout=30,
)
h = r.text
print("len", len(h))
for pat in ["graphql", "algolia", "woocommerce", "/api/", "search/products", "elastic"]:
    if pat in h.lower():
        print("found", pat)
for key in ["appId", "apiKey", "indexName", "ALGOLIA", "algolia"]:
    for m in re.finditer(rf"{key}['\"]?\s*[:=]\s*['\"]([^'\"]+)", h, re.I):
        print(key, m.group(1)[:80])
# algolia application id pattern
for m in re.finditer(r"([A-Z0-9]{8,12})", h):
    pass
idx = h.find("algolia")
if idx >= 0:
    print("snippet", h[idx : idx + 500])
