"""Menu Vision Parser — uses OpenRouter (Claude) to extract menu items from photos.

Sends up to 10 images in a single API call, returns structured menu data.
"""

import json
import logging
import re

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "anthropic/claude-sonnet-4-20250514"

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


def _build_openrouter_content(image_items: list[dict], source_type: str) -> list[dict]:
    """Build OpenRouter-compatible content array with images.

    Args:
        image_items: List of image data (URLs or base64)
        source_type: "url" or "base64"
    """
    content = []
    for i, img in enumerate(image_items[:10]):
        if source_type == "url":
            content.append({
                "type": "image_url",
                "image_url": {"url": img},
            })
        else:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['media_type']};base64,{img['data']}",
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
    return content


def _parse_response(data: dict) -> dict:
    """Extract JSON from OpenRouter response."""
    text = data["choices"][0]["message"]["content"].strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


async def _call_openrouter(content: list[dict], api_key: str) -> dict:
    """Make the OpenRouter API call."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "max_tokens": 4096,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()


async def parse_menu_photos(
    photo_urls: list[str],
    api_key: str,
) -> dict:
    """Parse menu items from photo URLs using OpenRouter (Claude Vision).

    Args:
        photo_urls: List of public image URLs (max 10)
        api_key: OpenRouter API key

    Returns:
        {"items": [...], "restaurant_name": str|None, "notes": str|None}
    """
    if not photo_urls:
        return {"items": [], "restaurant_name": None, "notes": "No photos provided"}

    content = _build_openrouter_content(photo_urls, "url")

    try:
        data = await _call_openrouter(content, api_key)
        result = _parse_response(data)
        logger.info("Parsed %d menu items from %d photos", len(result.get("items", [])), len(photo_urls))
        return result
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse Vision response as JSON")
        return {"items": [], "restaurant_name": None, "notes": f"JSON parse error: {str(e)}"}
    except Exception as e:
        logger.exception("OpenRouter Vision API call failed")
        return {"items": [], "restaurant_name": None, "notes": f"API error: {str(e)}"}


async def parse_menu_from_base64(
    images_b64: list[dict],
    api_key: str,
) -> dict:
    """Parse menu from base64-encoded images.

    Args:
        images_b64: [{"data": base64_str, "media_type": "image/jpeg"}, ...]
        api_key: OpenRouter API key
    """
    if not images_b64:
        return {"items": [], "restaurant_name": None, "notes": "No images provided"}

    content = _build_openrouter_content(images_b64, "base64")

    try:
        data = await _call_openrouter(content, api_key)
        result = _parse_response(data)
        logger.info("Parsed %d menu items from %d base64 images", len(result.get("items", [])), len(images_b64))
        return result
    except json.JSONDecodeError:
        logger.exception("Failed to parse Vision response as JSON")
        return {"items": [], "restaurant_name": None, "notes": "JSON parse error"}
    except Exception as e:
        logger.exception("OpenRouter Vision API call failed")
        return {"items": [], "restaurant_name": None, "notes": f"API error: {str(e)}"}
