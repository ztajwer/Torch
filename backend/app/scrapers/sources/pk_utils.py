from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from selectolax.parser import HTMLParser, Node


# Explicit Pakistani Rupee patterns only (never bare "74" from "4GB").
_PKR_PATTERNS = (
    re.compile(r"([\d,]+)\s*-\s*(?:PKR|Rs\.?)\b", re.I),
    re.compile(r"(?:Rs\.?|PKR)\s*([\d,]+)", re.I),
    re.compile(r"([\d]{1,3}(?:,\d{3})+)\s*(?:PKR|Rs)", re.I),
)

_PHONE_LIKE = re.compile(
    r"\b(galaxy|iphone|ipad|macbook|laptop|notebook|tablet|redmi|infinix|oppo|vivo|realme|pixel)\b",
    re.I,
)


def parse_pkr_price(text: str) -> Optional[float]:
    if not text:
        return None
    for pat in _PKR_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def sanitize_pkr_price(price: Optional[float], title: str = "") -> Optional[float]:
    """Drop bogus values (e.g. RAM/GB digits mistaken for price)."""
    if price is None:
        return None
    try:
        p = float(price)
    except (TypeError, ValueError):
        return None
    if p <= 0:
        return None
    t = title or ""
    # Phones/tablets/laptops in Pakistan are almost never under Rs 2,000 new.
    if _PHONE_LIKE.search(t) and p < 2000:
        return None
    # Accessories can be cheap; still reject tiny false positives on big titles.
    if len(t) > 40 and p < 150 and not re.search(r"\b(case|cable|cover|guard|film|strap)\b", t, re.I):
        return None
    return round(p, 2)


def price_from_mega_node(anchor: Node) -> Optional[float]:
    """Mega.pk puts '39,999 - PKR' on the product card container."""
    node: Optional[Node] = anchor
    for _ in range(14):
        if node is None:
            break
        cls = node.attributes.get("class") or ""
        if "lap_thu_box" in cls or "price" in cls.lower():
            p = parse_pkr_price(node.text(separator=" ", strip=True))
            if p is not None:
                return sanitize_pkr_price(p, anchor.text(strip=True) or "")
        node = node.parent
    return None


def first_img(node: Node, base_url: str) -> Optional[str]:
    for sel in ["amp-img", "img"]:
        img = node.css_first(sel)
        if img and img.attributes.get("src"):
            return urljoin(base_url, img.attributes["src"])
    return None


def format_pkr(amount: float | int | None) -> str:
    if amount is None:
        return "—"
    try:
        n = round(float(amount))
    except (TypeError, ValueError):
        return "—"
    if n <= 0:
        return "—"
    return f"Rs {n:,}"
