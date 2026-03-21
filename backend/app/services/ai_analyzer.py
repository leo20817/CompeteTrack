"""AI Analyzer — generates Traditional Chinese summaries for brand changes.

Uses Claude Sonnet API. If the call fails, returns None (caller sets ai_summary=NULL).
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-5-20241022"


async def generate_change_summary(change, api_key: str) -> Optional[str]:
    """Generate a Traditional Chinese summary for a single brand change.

    Args:
        change: BrandChange instance (not yet committed, but has all fields).
        api_key: Anthropic API key.

    Returns:
        Summary string in Traditional Chinese, or None on failure.
    """
    prompt = _build_prompt(change)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"].strip()
            return text
    except Exception:
        logger.exception("Failed to generate AI summary for %s", change.change_type)
        return None


def _build_prompt(change) -> str:
    """Build the prompt for Claude based on change type."""
    if change.change_type in ("price_increase", "price_decrease"):
        old_price = change.old_value.get("price", "?")
        new_price = change.new_value.get("price", "?")
        item_name = change.new_value.get("item_name", "?")
        pct = change.new_value.get("change_pct", "?")
        direction = "漲價" if change.change_type == "price_increase" else "降價"
        return (
            f"用繁體中文一句話描述：餐廳菜品「{item_name}」{direction}，"
            f"從 {old_price} 變為 {new_price}（變化 {pct}%）。"
            f"嚴重程度：{change.severity}。"
        )
    elif change.change_type == "new_item":
        item_name = change.new_value.get("item_name", "?")
        price = change.new_value.get("price", "未知")
        return (
            f"用繁體中文一句話描述：餐廳新增菜品「{item_name}」，"
            f"價格 {price}。"
        )
    elif change.change_type == "removed_item":
        item_name = change.old_value.get("item_name", "?")
        return (
            f"用繁體中文一句話描述：餐廳下架菜品「{item_name}」。"
        )
    else:
        return f"用繁體中文一句話描述這個變化：{change.change_type}，{change.field_changed}"
