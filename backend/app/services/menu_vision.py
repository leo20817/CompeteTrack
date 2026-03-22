"""Menu Vision Parser — uses Claude Vision to extract menu items from photos.

Sends up to 10 images in a single API call, returns structured menu data.
"""

import base64
import json
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-5-20241022"

SYSTEM_PROMPT = """你是一個越南餐廳菜單分析專家。從菜單照片中提取所有品項，回傳 JSON 格式。

規則：
1. 每個品項必須包含：item_name（品名）、category（分類）、price（價格，純數字，單位 VND）、description（描述，可為 null）
2. 價格統一轉換為整數 VND（例如 85.000đ → 85000）
3. 如果看不清價格，price 設為 null
4. 如果有分類標題（如「Phở」「Cơm」「Nước」），用它作為 category
5. 品名保持原文（越南文），不要翻譯
6. 如果有多張圖片，合併所有品項到同一個列表

回傳格式（純 JSON，不要 markdown）：
{
  "items": [
    {"item_name": "Phở Bò", "category": "Phở", "price": 65000, "description": null},
    {"item_name": "Gỏi Cuốn", "category": "Khai Vị", "price": 35000, "description": "2 cuốn"}
  ],
  "restaurant_name": "從照片中辨識的餐廳名（如有）",
  "notes": "任何需要人工確認的疑點"
}"""


async def parse_menu_photos(
    photo_urls: list[str],
    api_key: str,
) -> dict:
    """Parse menu items from photo URLs using Claude Vision.

    Args:
        photo_urls: List of public image URLs (max 10)
        api_key: Anthropic API key

    Returns:
        {"items": [...], "restaurant_name": str|None, "notes": str|None}
    """
    if not photo_urls:
        return {"items": [], "restaurant_name": None, "notes": "No photos provided"}

    # Build content with images
    content = []
    for i, url in enumerate(photo_urls[:10]):
        content.append({
            "type": "image",
            "source": {"type": "url", "url": url},
        })
        content.append({
            "type": "text",
            "text": f"（第 {i+1} 張菜單照片）",
        })

    content.append({
        "type": "text",
        "text": "請分析以上所有菜單照片，提取所有品項和價格，回傳 JSON。",
    })

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 4096,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": content}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"].strip()

            # Parse JSON from response (handle markdown code blocks)
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)
            logger.info("Parsed %d menu items from %d photos", len(result.get("items", [])), len(photo_urls))
            return result

    except json.JSONDecodeError as e:
        logger.exception("Failed to parse Claude Vision response as JSON")
        return {"items": [], "restaurant_name": None, "notes": f"JSON parse error: {str(e)}"}
    except Exception as e:
        logger.exception("Claude Vision API call failed")
        return {"items": [], "restaurant_name": None, "notes": f"API error: {str(e)}"}


async def parse_menu_from_base64(
    images_b64: list[dict],
    api_key: str,
) -> dict:
    """Parse menu from base64-encoded images.

    Args:
        images_b64: [{"data": base64_str, "media_type": "image/jpeg"}, ...]
        api_key: Anthropic API key
    """
    if not images_b64:
        return {"items": [], "restaurant_name": None, "notes": "No images provided"}

    content = []
    for i, img in enumerate(images_b64[:10]):
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["media_type"],
                "data": img["data"],
            },
        })
        content.append({
            "type": "text",
            "text": f"（第 {i+1} 張菜單照片）",
        })

    content.append({
        "type": "text",
        "text": "請分析以上所有菜單照片，提取所有品項和價格，回傳 JSON。",
    })

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 4096,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": content}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"].strip()

            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)
            logger.info("Parsed %d menu items from %d base64 images", len(result.get("items", [])), len(images_b64))
            return result

    except json.JSONDecodeError:
        logger.exception("Failed to parse Claude Vision response as JSON")
        return {"items": [], "restaurant_name": None, "notes": "JSON parse error"}
    except Exception as e:
        logger.exception("Claude Vision API call failed")
        return {"items": [], "restaurant_name": None, "notes": f"API error: {str(e)}"}
