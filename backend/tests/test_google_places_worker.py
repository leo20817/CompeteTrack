"""Tests for GooglePlacesWorker — all external calls mocked."""

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx

# Helper to create a mock response with a request attached
def _mock_response(status_code: int, json_data: dict) -> httpx.Response:
    request = httpx.Request("GET", "https://maps.googleapis.com/maps/api/place/details/json")
    return httpx.Response(status_code, json=json_data, request=request)
import pytest

from app.workers.google_places import GooglePlacesWorker


@pytest.mark.asyncio
async def test_collect_happy_path(places_response):
    """Worker returns parsed data from a successful API response."""
    mock_response = _mock_response(200, places_response)

    brand_id = uuid4()
    async with GooglePlacesWorker("fake-key") as worker:
        worker.client.get = AsyncMock(return_value=mock_response)
        result = await worker.collect(brand_id, "ChIJtest123", date(2026, 3, 21))

    assert result["raw_data"]["status"] == "OK"
    assert result["rating"] == 4.1
    assert result["user_ratings_total"] == 892
    assert result["popular_times"] is None  # not available in official API
    assert isinstance(result["hours_data"], dict)
    assert "monday" in result["hours_data"]
    assert result["hours_data"]["monday"]["is_closed"] is False


@pytest.mark.asyncio
async def test_collect_no_hours(places_empty_response):
    """Worker handles missing opening_hours gracefully."""
    mock_response = _mock_response(200, places_empty_response)

    async with GooglePlacesWorker("fake-key") as worker:
        worker.client.get = AsyncMock(return_value=mock_response)
        result = await worker.collect(uuid4(), "ChIJtest456", date(2026, 3, 21))

    assert result["hours_data"] == {}
    assert result["menu_items"] == []
    assert result["rating"] == 3.5


@pytest.mark.asyncio
async def test_collect_not_found(places_not_found_response):
    """Worker raises ValueError for NOT_FOUND place_id."""
    mock_response = _mock_response(200, places_not_found_response)

    async with GooglePlacesWorker("fake-key") as worker:
        worker.client.get = AsyncMock(return_value=mock_response)
        with pytest.raises(ValueError, match="Place not found"):
            await worker.collect(uuid4(), "ChIJbad_id", date(2026, 3, 21))


@pytest.mark.asyncio
async def test_collect_request_denied(places_denied_response):
    """Worker raises ValueError for REQUEST_DENIED."""
    mock_response = _mock_response(200, places_denied_response)

    async with GooglePlacesWorker("fake-key") as worker:
        worker.client.get = AsyncMock(return_value=mock_response)
        with pytest.raises(ValueError, match="API request denied"):
            await worker.collect(uuid4(), "ChIJtest123", date(2026, 3, 21))


@pytest.mark.asyncio
async def test_collect_no_place_id():
    """Worker raises ValueError when place_id is empty."""
    async with GooglePlacesWorker("fake-key") as worker:
        with pytest.raises(ValueError, match="has no google_place_id"):
            await worker.collect(uuid4(), "", date(2026, 3, 21))


@pytest.mark.asyncio
async def test_parse_hours_with_periods(places_response):
    """Hours parser correctly maps Google day indices to day names."""
    worker = GooglePlacesWorker("fake-key")
    result_data = places_response["result"]
    hours = worker._parse_hours(result_data)

    # Google: day=1 is Monday
    assert hours["monday"]["open"] == "06:00"
    assert hours["monday"]["close"] == "22:00"
    assert hours["monday"]["is_closed"] is False

    # Google: day=6 is Saturday
    assert hours["saturday"]["open"] == "06:00"
    assert hours["saturday"]["close"] == "23:00"

    # Google: day=0 is Sunday
    assert hours["sunday"]["open"] == "06:00"
    assert hours["sunday"]["close"] == "23:00"


@pytest.mark.asyncio
async def test_parse_hours_weekday_text_fallback():
    """Hours parser falls back to weekday_text when no periods."""
    worker = GooglePlacesWorker("fake-key")
    result_data = {
        "opening_hours": {
            "weekday_text": [
                "Monday: 8:00 AM – 9:00 PM",
                "Tuesday: Closed",
            ]
        }
    }
    hours = worker._parse_hours(result_data)

    assert hours["monday"]["raw_text"] == "8:00 AM – 9:00 PM"
    assert hours["monday"]["is_closed"] is False
    assert hours["tuesday"]["is_closed"] is True


@pytest.mark.asyncio
async def test_menu_items_always_empty():
    """Google Places API does not provide menu data — always returns []."""
    worker = GooglePlacesWorker("fake-key")
    items = worker._parse_menu({"name": "Test"}, date(2026, 3, 21))
    assert items == []
