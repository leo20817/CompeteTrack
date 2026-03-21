"""Tests for POST /api/brands/{id}/collect endpoint."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.brand import Brand


@pytest.mark.asyncio
async def test_collect_happy_path(client, sample_brand, places_response):
    """Collect creates menu_snapshot and hours_snapshot records."""
    with patch("app.api.collect.GooglePlacesWorker") as MockWorker:
        mock_instance = AsyncMock()
        mock_instance.collect.return_value = {
            "raw_data": places_response,
            "hours_data": {"monday": {"open": "06:00", "close": "22:00", "is_closed": False}},
            "popular_times": None,
            "menu_items": [],
            "rating": 4.1,
            "user_ratings_total": 892,
        }
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockWorker.return_value = mock_instance

        with patch("app.api.collect.settings") as mock_settings:
            mock_settings.google_places_api_key = "fake-key"

            resp = await client.post(f"/api/brands/{sample_brand.id}/collect")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["brand_id"] == str(sample_brand.id)
    assert data["data"]["menu_snapshot_id"] is not None
    assert data["data"]["has_hours_data"] is True
    assert data["data"]["rating"] == 4.1


@pytest.mark.asyncio
async def test_collect_no_menu_creates_empty_snapshot(client, sample_brand, places_empty_response):
    """Collect still creates a snapshot even when no menu data."""
    with patch("app.api.collect.GooglePlacesWorker") as MockWorker:
        mock_instance = AsyncMock()
        mock_instance.collect.return_value = {
            "raw_data": places_empty_response,
            "hours_data": {},
            "popular_times": None,
            "menu_items": [],
            "rating": 3.5,
            "user_ratings_total": 100,
        }
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockWorker.return_value = mock_instance

        with patch("app.api.collect.settings") as mock_settings:
            mock_settings.google_places_api_key = "fake-key"

            resp = await client.post(f"/api/brands/{sample_brand.id}/collect")

    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["menu_items_count"] == 0
    assert data["data"]["has_hours_data"] is False


@pytest.mark.asyncio
async def test_collect_brand_not_found(client):
    """Collect returns 404 for non-existent brand."""
    fake_id = uuid4()

    with patch("app.api.collect.settings") as mock_settings:
        mock_settings.google_places_api_key = "fake-key"
        resp = await client.post(f"/api/brands/{fake_id}/collect")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_collect_no_place_id(client, brand_no_place_id):
    """Collect returns 422 when brand has no google_place_id."""
    with patch("app.api.collect.settings") as mock_settings:
        mock_settings.google_places_api_key = "fake-key"
        resp = await client.post(f"/api/brands/{brand_no_place_id.id}/collect")

    assert resp.status_code == 422
    assert "google_place_id" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_collect_no_api_key(client, sample_brand):
    """Collect returns 500 when API key is not configured."""
    with patch("app.api.collect.settings") as mock_settings:
        mock_settings.google_places_api_key = None
        resp = await client.post(f"/api/brands/{sample_brand.id}/collect")

    assert resp.status_code == 500
    assert "GOOGLE_PLACES_API_KEY" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_collect_twice_creates_two_snapshots(client, sample_brand, places_response):
    """Running collect twice creates 2 separate snapshots (immutable)."""
    with patch("app.api.collect.GooglePlacesWorker") as MockWorker:
        mock_instance = AsyncMock()
        mock_instance.collect.return_value = {
            "raw_data": places_response,
            "hours_data": {"monday": {"open": "06:00", "close": "22:00", "is_closed": False}},
            "popular_times": None,
            "menu_items": [],
            "rating": 4.1,
            "user_ratings_total": 892,
        }
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockWorker.return_value = mock_instance

        with patch("app.api.collect.settings") as mock_settings:
            mock_settings.google_places_api_key = "fake-key"

            resp1 = await client.post(f"/api/brands/{sample_brand.id}/collect")
            resp2 = await client.post(f"/api/brands/{sample_brand.id}/collect")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # Each collect creates a unique snapshot
    snap_id_1 = resp1.json()["data"]["menu_snapshot_id"]
    snap_id_2 = resp2.json()["data"]["menu_snapshot_id"]
    assert snap_id_1 != snap_id_2
