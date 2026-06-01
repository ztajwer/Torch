from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from app.ai.gemini_advisor import _prefer_pk_products
from app.api.utils import apply_filters
from app.config import settings
from app.pipeline.query_intent import rank_products_by_intent
from app.pipeline.search_match import filter_products_for_query
from app.scrapers.sources.pk_utils import format_pkr

log = logging.getLogger("torch.ai.chat")

_OFF_TOPIC_RE = re.compile(
    r"\b(homework|essay|assignment|write (?:me )?(?:a )?(?:poem|story|code)|"
    r"python script|javascript|weather forecast|who is the president|"
    r"translate this|solve this math|2\+2|bitcoin|crypto trading|"
    r"medical advice|diagnose|recipe for)\b",
    re.I,
)

_GREETING_RE = re.compile(r"^\s*(hi|hello|hey|salam|aoa|assalam|good\s+(morning|evening))\b", re.I)


def _chat_product_row(p: dict) -> dict[str, Any]:
    return {
        "id": p.get("id"),
        "title": p.get("product_title"),
        "price_pkr": p.get("price"),
        "store": p.get("marketplace"),
        "rating": p.get("rating"),
        "reviews": p.get("review_count"),
        "category": p.get("category"),
        "url": p.get("product_url"),
    }


def _is_generic_shopping(msg: str) -> bool:
    lower = msg.lower().strip()
    if _GREETING_RE.search(lower):
        return True
    hints = (
        "what can you",
        "what do you",
        "help me shop",
        "help me buy",
        "recommend",
        "suggest",
        "show me",
        "what is torch",
        "how does torch",
        "which store",
        "stores do you",
    )
    return any(h in lower for h in hints)


def _products_for_context(
    products: list[dict],
    message: str,
    context_query: str | None,
) -> list[dict]:
    pk = _prefer_pk_products(products)
    if not pk:
        return []

    seen: set[str] = set()
    out: list[dict] = []

    def add_list(items: list[dict]) -> None:
        for p in items:
            pid = str(p.get("id") or "")
            if pid and pid not in seen:
                seen.add(pid)
                out.append(p)

    queries: list[str] = []
    if context_query and context_query.strip():
        queries.append(context_query.strip())
    if message.strip():
        queries.append(message.strip())

    for q in queries:
        add_list(filter_products_for_query(pk, q))
        if len(out) >= 18:
            break

    if len(out) < 4:
        add_list(apply_filters(pk, q=message.strip()))

    if len(out) < 4:
        ranked = rank_products_by_intent(pk, message, min_relevance=8.0)
        add_list(ranked[:15])

    if len(out) < 3 and _is_generic_shopping(message):
        trending = sorted(pk, key=lambda x: float(x.get("trend_score") or 0), reverse=True)
        add_list(trending[:12])

    return out[:20]


def _call_gemini_chat(system: str, user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system,
    )
    try:
        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.35,
                max_output_tokens=1024,
            ),
        )
    except TypeError:
        response = model.generate_content(user_prompt)
    return (response.text or "").strip()


def _fallback_reply(message: str, context: list[dict]) -> dict[str, Any]:
    if _OFF_TOPIC_RE.search(message):
        return {
            "reply": (
                "I can only help with **products and prices** on TORCH "
                "(Daraz, PriceOye, Telemart, Mega.pk, Shophive). "
                "Try asking about a product — e.g. “best phone under 80,000 PKR”."
            ),
            "powered_by": "torch-rules",
            "refused": True,
            "products": [],
        }

    if _GREETING_RE.search(message) or _is_generic_shopping(message):
        intro = (
            "Hi! I'm the **TORCH shopping assistant**. I answer questions about products "
            "in our catalog — prices in **PKR**, store comparison, and buying advice.\n\n"
            "Use **Analyze Now** on Home to search live, or ask me about items already in the catalog."
        )
        if context:
            intro += "\n\n**Sample from catalog:**"
            for p in context[:3]:
                intro += f"\n• {p.get('product_title')} — {format_pkr(p.get('price'))} ({p.get('marketplace')})"
        return {"reply": intro, "powered_by": "torch-rules", "refused": False, "products": [_chat_product_row(p) for p in context[:5]]}

    if not context:
        return {
            "reply": (
                f"I don't have matching products for “{message.strip()}” in the saved catalog yet.\n\n"
                "Go to **Home**, type that product name, and tap **Analyze Now** — "
                "then ask me again and I can compare picks for you."
            ),
            "powered_by": "torch-rules",
            "refused": False,
            "products": [],
        }

    lines = [f"Here are matches for “{message.strip()}” from the TORCH catalog (PKR):\n"]
    for i, p in enumerate(context[:5], 1):
        lines.append(
            f"{i}. **{p.get('product_title')}** — {format_pkr(p.get('price'))} on {p.get('marketplace')}"
            + (f" (★ {p.get('rating')})" if p.get("rating") else "")
        )
    lines.append("\nFor live prices across all stores, use **Analyze Now** on Home.")
    return {
        "reply": "\n".join(lines),
        "powered_by": "torch-rules",
        "refused": False,
        "products": [_chat_product_row(p) for p in context[:8]],
    }


def _build_system_prompt(product_rows: list[dict]) -> str:
    data = json.dumps(product_rows, ensure_ascii=False, indent=0)
    if not product_rows:
        catalog_note = "The catalog is currently EMPTY. Tell the user to run Analyze Now on Home to search stores."
    else:
        catalog_note = f"{len(product_rows)} products provided below — use ONLY these for specifics."

    return f"""You are TORCH Shop Assistant — a specialist for Pakistani online shopping ONLY.

STRICT RULES (never break):
1. Answer ONLY about: products, prices in PKR, comparisons, stores (Daraz, PriceOye, Telemart, Mega.pk, Shophive), using TORCH (search, trending, compare, products pages).
2. Use ONLY facts from PRODUCT DATA JSON. Never invent product names, prices, or URLs.
3. If asked anything else (homework, coding, weather, politics, health, general trivia, jokes unrelated to shopping): reply briefly that you only help with TORCH product shopping and suggest a product question.
4. All money is PKR. Never use $ or USD.
5. Be warm, concise, use short paragraphs or bullets. Mention store names when comparing.
6. If catalog is empty or no match, tell user to search on Home with Analyze Now.
7. {catalog_note}

PRODUCT DATA (JSON):
{data}
"""


def _format_history(history: list[dict[str, str]], max_turns: int = 6) -> str:
    if not history:
        return ""
    tail = history[-max_turns * 2 :]
    lines = []
    for h in tail:
        role = h.get("role", "user")
        content = (h.get("content") or "").strip()[:800]
        if not content:
            continue
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")
    return "\n".join(lines)


async def product_chat_reply(
    *,
    message: str,
    history: list[dict[str, str]],
    products: list[dict],
    context_query: str | None = None,
) -> dict[str, Any]:
    msg = message.strip()
    if len(msg) < 1:
        return {"reply": "Please type a product question.", "powered_by": "none", "products": [], "refused": False}

    if _OFF_TOPIC_RE.search(msg):
        return {
            "reply": (
                "I'm built only for **TORCH product shopping** in Pakistan — prices, comparisons, and buy advice.\n\n"
                "Ask me something like: “Which is cheaper for iPhone 15?” or “Best laptop under 150,000 PKR?”"
            ),
            "powered_by": "torch-rules",
            "refused": True,
            "products": [],
        }

    context_products = _products_for_context(products, msg, context_query)
    product_rows = [_chat_product_row(p) for p in context_products]

    if not settings.gemini_api_key:
        return _fallback_reply(msg, context_products)

    try:
        import google.generativeai as genai  # noqa: F401
    except ImportError:
        return _fallback_reply(msg, context_products)

    system = _build_system_prompt(product_rows)
    hist = _format_history(history)
    user_block = f"Conversation so far:\n{hist}\n\n" if hist else ""
    user_prompt = (
        f"{user_block}Latest user message:\n{msg}\n\n"
        "Reply as TORCH Shop Assistant (products & shopping only):"
    )

    try:
        reply = await asyncio.to_thread(_call_gemini_chat, system, user_prompt)
        reply = reply.strip() or _fallback_reply(msg, context_products)["reply"]
        reply = re.sub(r"\$\s*[\d,.]+", "", reply)
        return {
            "reply": reply,
            "powered_by": "gemini",
            "refused": False,
            "products": product_rows[:8],
        }
    except Exception as e:
        log.exception("chat failed: %s", e)
        fb = _fallback_reply(msg, context_products)
        fb["reply"] = fb["reply"] + "\n\n_(AI temporarily unavailable — showing catalog matches.)_"
        return fb
