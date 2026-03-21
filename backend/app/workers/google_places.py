import logging
from datetime import date
from uuid import UUID

import httpx

from app.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

# Fields to request from Google Places API
PLACE_DETAILS_FIELDS = [
    "name",
    "opening_hours",
    "current_opening_hours",
    "rating",
    "user_ratings_total",
    "price_level",
    "formatted_address",
    "formatted_phone_number",
    "website",
    "url",
    "menu",
]


class GooglePlacesWorker(BaseWorker):
    """Fetches place details from Google Places API."""

    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    async def collect(self, brand_id: UUID, place_id: str, snapshot_date: date) -> dict:
        """
        Fetch place details from Google Places API.

        Returns:
            {
                "raw_data": dict,       # full API response
                "hours_data": dict,     # parsed opening hours or {}
                "popular_times": None,  # not available in official API
                "menu_items": list,     # parsed menu items (usually empty)
                "rating": float | None,
                "user_ratings_total": int | None,
            }
        """
        if not place_id:
            raise ValueError(f"Brand {brand_id} has no google_place_id")

        raw_data = await self._fetch_place_details(place_id)

        result = raw_data.get("result", {})

        hours_data = self._parse_hours(result)
        menu_items = self._parse_menu(result, snapshot_date)
        rating = result.get("rating")
        user_ratings_total = result.get("user_ratings_total")

        if not menu_items:
            logger.warning(
                "No menu data available for brand %s (place_id: %s)",
                brand_id, place_id,
            )

        return {
            "raw_data": raw_data,
            "hours_data": hours_data,
            "popular_times": None,  # Not available in official API
            "menu_items": menu_items,
            "rating": rating,
            "user_ratings_total": user_ratings_total,
        }

    async def _fetch_place_details(self, place_id: str) -> dict:
        """Call Google Places API Place Details endpoint."""
        params = {
            "place_id": place_id,
            "fields": ",".join(PLACE_DETAILS_FIELDS),
            "key": self.api_key,
            "language": "vi",  # Vietnamese for local menu names
        }

        response = await self.client.get(self.DETAILS_URL, params=params)
        response.raise_for_status()
        data = response.json()

        status = data.get("status")
        if status == "INVALID_REQUEST":
            raise ValueError(f"Invalid place_id: {place_id}")
        if status == "NOT_FOUND":
            raise ValueError(f"Place not found: {place_id}")
        if status == "REQUEST_DENIED":
            raise ValueError(f"API request denied — check GOOGLE_PLACES_API_KEY")
        if status != "OK":
            raise ValueError(f"Google Places API error: {status} — {data.get('error_message', '')}")

        return data

    def _parse_hours(self, result: dict) -> dict:
        """Parse opening_hours into {day: {open, close, is_closed}} format."""
        opening_hours = result.get("opening_hours") or result.get("current_opening_hours")
        if not opening_hours:
            return {}

        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        hours_data = {}

        periods = opening_hours.get("periods", [])
        if not periods:
            # Use weekday_text as fallback
            for text in opening_hours.get("weekday_text", []):
                # e.g. "Monday: 10:00 AM – 10:00 PM"
                parts = text.split(": ", 1)
                if len(parts) == 2:
                    day_key = parts[0].strip().lower()
                    hours_data[day_key] = {"raw_text": parts[1].strip(), "is_closed": "Closed" in parts[1]}
            return hours_data

        # Initialize all days as closed
        for day in day_names:
            hours_data[day] = {"open": None, "close": None, "is_closed": True}

        for period in periods:
            open_info = period.get("open", {})
            close_info = period.get("close", {})

            day_index = open_info.get("day", 0)
            # Google uses 0=Sunday, we use 0=Monday
            adjusted_index = (day_index - 1) % 7
            day_name = day_names[adjusted_index]

            open_time = open_info.get("time", "")
            close_time = close_info.get("time", "")

            # Format as HH:MM
            open_formatted = f"{open_time[:2]}:{open_time[2:]}" if len(open_time) == 4 else open_time
            close_formatted = f"{close_time[:2]}:{close_time[2:]}" if len(close_time) == 4 else close_time

            hours_data[day_name] = {
                "open": open_formatted,
                "close": close_formatted,
                "is_closed": False,
            }

        return hours_data

    def _parse_menu(self, result: dict, snapshot_date: date) -> list[dict]:
        """
        Parse menu items from API response.

        Google Places API does not provide structured menu data.
        This returns an empty list — menu data will come from
        Foody.vn scraper (Phase 6) or manual entry.
        """
        # The Places API doesn't return menu items.
        # Future: could parse from website_url or other sources.
        return []
