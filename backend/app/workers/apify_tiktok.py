"""TikTok data collector via Apify REST API."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

ACTOR_ID = "clockworks~free-tiktok-scraper"
APIFY_RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


async def collect_tiktok(
    username: str,
    brand_id: UUID,
    api_token: str,
    snapshot_date: Optional[date] = None,
) -> dict:
    """Fetch TikTok profile data via Apify.

    Returns:
        {
            "followers": int,
            "following": int,
            "total_posts": int,
            "metrics": {total_likes, video_count, avg_views, ...},
            "top_posts": [top 3 by views],
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
                "profiles": [f"@{clean_username}"],
                "resultsPerPage": 10,
                "shouldDownloadVideos": False,
            },
        )
        resp.raise_for_status()
        items = resp.json()

    if not items:
        logger.warning("Apify TikTok returned no data for @%s", clean_username)
        return _empty_result()

    # First item is usually the profile + videos
    profile = None
    videos = []

    for item in items:
        if item.get("type") == "user" or "fans" in item or "followerCount" in item:
            profile = item
        elif item.get("type") == "video" or "playCount" in item:
            videos.append(item)

    # If no explicit profile found, try to extract from first item
    if not profile and items:
        profile = items[0]

    followers = profile.get("fans") or profile.get("followerCount") or 0
    following = profile.get("following") or profile.get("followingCount") or 0
    total_likes = profile.get("hearts") or profile.get("heartCount") or profile.get("diggCount") or 0
    video_count = profile.get("videoCount") or len(videos)

    # Calculate averages from videos
    views = [v.get("playCount") or v.get("views") or 0 for v in videos]
    likes = [v.get("diggCount") or v.get("likes") or 0 for v in videos]
    comments = [v.get("commentCount") or v.get("comments") or 0 for v in videos]
    shares = [v.get("shareCount") or v.get("shares") or 0 for v in videos]

    n = len(videos) or 1
    avg_views = sum(views) / n
    avg_likes = sum(likes) / n
    avg_comments = sum(comments) / n
    avg_shares = sum(shares) / n
    engagement_rate = (avg_likes + avg_comments + avg_shares) / max(followers, 1) * 100

    # Top 3 videos by views
    sorted_videos = sorted(videos, key=lambda v: v.get("playCount") or v.get("views") or 0, reverse=True)[:3]
    top_posts = []
    for v in sorted_videos:
        top_posts.append({
            "id": v.get("id") or v.get("videoId", ""),
            "description": (v.get("text") or v.get("desc") or "")[:100],
            "views": v.get("playCount") or v.get("views") or 0,
            "likes": v.get("diggCount") or v.get("likes") or 0,
            "comments": v.get("commentCount") or v.get("comments") or 0,
            "thumbnail": v.get("thumbnailUrl") or v.get("cover") or "",
            "url": v.get("webVideoUrl") or f"https://tiktok.com/@{clean_username}/video/{v.get('id', '')}",
        })

    return {
        "followers": followers,
        "following": following,
        "total_posts": video_count,
        "metrics": {
            "total_likes": total_likes,
            "video_count": video_count,
            "avg_views": round(avg_views),
            "avg_likes": round(avg_likes),
            "avg_comments": round(avg_comments),
            "avg_shares": round(avg_shares),
            "engagement_rate": round(engagement_rate, 2),
        },
        "top_posts": top_posts,
    }


def _empty_result() -> dict:
    return {
        "followers": 0,
        "following": 0,
        "total_posts": 0,
        "metrics": {
            "total_likes": 0, "video_count": 0, "avg_views": 0,
            "avg_likes": 0, "avg_comments": 0, "avg_shares": 0,
            "engagement_rate": 0,
        },
        "top_posts": [],
    }
