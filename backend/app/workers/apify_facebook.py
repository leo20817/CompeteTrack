"""Facebook page data collector via Apify REST API."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

ACTOR_ID = "apify~facebook-pages-scraper"
APIFY_RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


async def collect_facebook(
    page_url: str,
    brand_id: UUID,
    api_token: str,
    snapshot_date: Optional[date] = None,
) -> dict:
    """Fetch Facebook page data via Apify.

    Returns:
        {
            "followers": int,
            "following": None,
            "total_posts": None,
            "metrics": {page_likes, rating, review_count, checkins, talking_about},
            "top_posts": None,
        }
    """
    if not snapshot_date:
        snapshot_date = date.today()

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            APIFY_RUN_URL,
            params={"token": api_token},
            json={
                "startUrls": [{"url": page_url}],
                "maxPosts": 0,
            },
        )
        resp.raise_for_status()
        items = resp.json()

    if not items:
        logger.warning("Apify Facebook returned no data for %s", page_url)
        return _empty_result()

    page = items[0]

    page_likes = page.get("likes") or page.get("pageLikes") or 0
    followers = page.get("followers") or page.get("followersCount") or page_likes
    rating = page.get("overallStarRating") or page.get("rating")
    review_count = page.get("ratingCount") or page.get("reviewCount") or 0
    checkins = page.get("checkins") or page.get("wereHereCount") or 0
    talking_about = page.get("talkingAboutCount") or page.get("talkingAbout") or 0

    return {
        "followers": followers,
        "following": None,
        "total_posts": None,
        "metrics": {
            "page_likes": page_likes,
            "rating": float(rating) if rating else None,
            "review_count": review_count,
            "checkins": checkins,
            "talking_about": talking_about,
        },
        "top_posts": None,
    }


def _empty_result() -> dict:
    return {
        "followers": 0,
        "following": None,
        "total_posts": None,
        "metrics": {
            "page_likes": 0, "rating": None, "review_count": 0,
            "checkins": 0, "talking_about": 0,
        },
        "top_posts": None,
    }
