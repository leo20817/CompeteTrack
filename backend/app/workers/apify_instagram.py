"""Instagram data collector via Apify REST API."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

ACTOR_ID = "apify~instagram-profile-scraper"
APIFY_RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


async def collect_instagram(
    username: str,
    brand_id: UUID,
    api_token: str,
    snapshot_date: Optional[date] = None,
) -> dict:
    """Fetch Instagram profile data via Apify.

    Returns:
        {
            "followers": int,
            "following": int,
            "total_posts": int,
            "metrics": {avg_likes, avg_comments, engagement_rate, ...},
            "top_posts": [top 3 by likes],
        }
    """
    if not snapshot_date:
        snapshot_date = date.today()

    clean_username = username.lstrip("@")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            APIFY_RUN_URL,
            params={"token": api_token},
            json={
                "usernames": [clean_username],
                "resultsLimit": 10,
            },
        )
        resp.raise_for_status()
        items = resp.json()

    if not items:
        logger.warning("Apify Instagram returned no data for %s", clean_username)
        return _empty_result()

    profile = items[0]

    followers = profile.get("followersCount") or profile.get("followers") or 0
    following = profile.get("followsCount") or profile.get("following") or 0
    total_posts = profile.get("postsCount") or profile.get("posts") or 0

    # Get recent posts
    posts = profile.get("latestPosts") or profile.get("posts") or []
    if isinstance(posts, int):
        posts = []

    likes = [p.get("likesCount") or p.get("likes") or 0 for p in posts]
    comments = [p.get("commentsCount") or p.get("comments") or 0 for p in posts]

    n = len(posts) or 1
    avg_likes = sum(likes) / n
    avg_comments = sum(comments) / n
    engagement_rate = (avg_likes + avg_comments) / max(followers, 1) * 100

    # Count reels
    reels = [p for p in posts if p.get("type") == "Video" or p.get("isVideo")]
    reel_views = [p.get("videoViewCount") or p.get("views") or 0 for p in reels]
    avg_reel_views = sum(reel_views) / max(len(reels), 1)

    # Top 3 posts by likes
    sorted_posts = sorted(posts, key=lambda p: p.get("likesCount") or p.get("likes") or 0, reverse=True)[:3]
    top_posts = []
    for p in sorted_posts:
        top_posts.append({
            "id": p.get("id") or p.get("shortCode") or "",
            "description": (p.get("caption") or "")[:100],
            "likes": p.get("likesCount") or p.get("likes") or 0,
            "comments": p.get("commentsCount") or p.get("comments") or 0,
            "thumbnail": p.get("displayUrl") or p.get("thumbnailUrl") or "",
            "url": p.get("url") or f"https://instagram.com/p/{p.get('shortCode', '')}",
        })

    return {
        "followers": followers,
        "following": following,
        "total_posts": total_posts,
        "metrics": {
            "avg_likes": round(avg_likes),
            "avg_comments": round(avg_comments),
            "engagement_rate": round(engagement_rate, 2),
            "reels_count": len(reels),
            "avg_reel_views": round(avg_reel_views),
        },
        "top_posts": top_posts,
    }


def _empty_result() -> dict:
    return {
        "followers": 0,
        "following": 0,
        "total_posts": 0,
        "metrics": {
            "avg_likes": 0, "avg_comments": 0, "engagement_rate": 0,
            "reels_count": 0, "avg_reel_views": 0,
        },
        "top_posts": [],
    }
