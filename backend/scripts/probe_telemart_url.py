import json

import httpx

APP = "7Z6UNQYQER"
KEY = "9b4c33f99e845fe1363fd4c6ceb0f467"
headers = {
    "X-Algolia-Application-Id": APP,
    "X-Algolia-API-Key": KEY,
    "Content-Type": "application/json",
}
body = {"requests": [{"indexName": "products", "params": "query=iphone&hitsPerPage=1"}]}
hit = httpx.post(
    f"https://{APP}-dsn.algolia.net/1/indexes/*/queries",
    headers=headers,
    json=body,
    timeout=20,
).json()["results"][0]["hits"][0]
print(json.dumps(hit, indent=2)[:2000])
slug = hit.get("slug")
for path in [slug, f"products/{slug}", f"product/{slug}", f"{slug}.html"]:
    u = f"https://www.telemart.pk/{path}"
    r = httpx.get(u, follow_redirects=True, timeout=15)
    print(r.status_code, u, "->", r.url)
