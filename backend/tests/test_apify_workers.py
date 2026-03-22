"""Tests for Apify social media workers — all API calls mocked."""

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from app.workers.apify_tiktok import collect_tiktok
from app.workers.apify_instagram import collect_instagram
from app.workers.apify_facebook import collect_facebook


def _mock_response(status_code: int, json_data) -> httpx.Response:
    request = httpx.Request("POST", "https://api.apify.com/v2/acts/test/run-sync-get-dataset-items")
    return httpx.Response(status_code, json=json_data, request=request)


# ── TikTok Tests ──

TIKTOK_RESPONSE = [
    {
        "type": "user",
        "fans": 15000,
        "following": 200,
        "hearts": 500000,
        "videoCount": 120,
    },
    {
        "type": "video",
        "id": "v1",
        "text": "Best pho in town",
        "playCount": 250000,
        "diggCount": 8000,
        "commentCount": 300,
        "shareCount": 150,
        "cover": "https://example.com/thumb1.jpg",
    },
    {
        "type": "video",
        "id": "v2",
        "text": "New menu item",
        "playCount": 50000,
        "diggCount": 2000,
        "commentCount": 100,
        "shareCount": 50,
        "cover": "https://example.com/thumb2.jpg",
    },
    {
        "type": "video",
        "id": "v3",
        "text": "Kitchen tour",
        "playCount": 120000,
        "diggCount": 5000,
        "commentCount": 200,
        "shareCount": 80,
        "cover": "https://example.com/thumb3.jpg",
    },
]


@pytest.mark.asyncio
@patch("app.workers.apify_tiktok.httpx.AsyncClient")
async def test_tiktok_happy_path(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, TIKTOK_RESPONSE)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_tiktok("pho24", uuid4(), "fake-token")

    assert result["followers"] == 15000
    assert result["following"] == 200
    assert result["metrics"]["total_likes"] == 500000
    assert result["metrics"]["video_count"] == 120
    assert result["metrics"]["avg_views"] > 0
    assert result["metrics"]["engagement_rate"] > 0
    assert len(result["top_posts"]) == 3
    # Top post by views should be v1 (250,000)
    assert result["top_posts"][0]["views"] == 250000


@pytest.mark.asyncio
@patch("app.workers.apify_tiktok.httpx.AsyncClient")
async def test_tiktok_empty_response(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, [])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_tiktok("nobody", uuid4(), "fake-token")

    assert result["followers"] == 0
    assert result["top_posts"] == []


# ── Instagram Tests ──

IG_RESPONSE = [
    {
        "followersCount": 8500,
        "followsCount": 300,
        "postsCount": 200,
        "latestPosts": [
            {"id": "p1", "likesCount": 1200, "commentsCount": 50, "type": "Image", "shortCode": "abc1", "caption": "Delicious pho"},
            {"id": "p2", "likesCount": 800, "commentsCount": 30, "type": "Video", "isVideo": True, "videoViewCount": 5000, "shortCode": "abc2", "caption": "New reel"},
            {"id": "p3", "likesCount": 2000, "commentsCount": 80, "type": "Image", "shortCode": "abc3", "caption": "Grand opening"},
        ],
    }
]


@pytest.mark.asyncio
@patch("app.workers.apify_instagram.httpx.AsyncClient")
async def test_instagram_happy_path(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, IG_RESPONSE)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_instagram("pho24", uuid4(), "fake-token")

    assert result["followers"] == 8500
    assert result["following"] == 300
    assert result["metrics"]["avg_likes"] > 0
    assert result["metrics"]["reels_count"] == 1
    assert result["metrics"]["engagement_rate"] > 0
    assert len(result["top_posts"]) == 3
    # Top post by likes should be p3 (2000)
    assert result["top_posts"][0]["likes"] == 2000


@pytest.mark.asyncio
@patch("app.workers.apify_instagram.httpx.AsyncClient")
async def test_instagram_empty(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, [])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_instagram("nobody", uuid4(), "fake-token")
    assert result["followers"] == 0


# ── Facebook Tests ──

FB_RESPONSE = [
    {
        "likes": 5000,
        "followers": 5200,
        "overallStarRating": 4.3,
        "ratingCount": 120,
        "checkins": 800,
        "talkingAboutCount": 150,
    }
]


@pytest.mark.asyncio
@patch("app.workers.apify_facebook.httpx.AsyncClient")
async def test_facebook_happy_path(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, FB_RESPONSE)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_facebook("https://facebook.com/pho24", uuid4(), "fake-token")

    assert result["followers"] == 5200
    assert result["metrics"]["page_likes"] == 5000
    assert result["metrics"]["rating"] == 4.3
    assert result["metrics"]["review_count"] == 120
    assert result["metrics"]["checkins"] == 800
    assert result["top_posts"] is None


@pytest.mark.asyncio
@patch("app.workers.apify_facebook.httpx.AsyncClient")
async def test_facebook_empty(MockClient):
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_response(200, [])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    MockClient.return_value = mock_client

    result = await collect_facebook("https://facebook.com/nobody", uuid4(), "fake-token")
    assert result["followers"] == 0
    assert result["metrics"]["rating"] is None
