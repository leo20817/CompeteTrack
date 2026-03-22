import logging
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.brand import Brand, MenuSnapshot, MenuItem, HoursSnapshot
from app.schemas.response import APIResponse
from app.workers.google_places import GooglePlacesWorker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["collect"])


@router.post("/{brand_id}/collect")
async def collect_brand_data(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually trigger data collection for a single brand."""

    # 1. Get the brand
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if not brand.google_place_id:
        raise HTTPException(
            status_code=422,
            detail="Brand has no google_place_id — cannot collect from Google Places",
        )

    if not settings.google_places_api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_PLACES_API_KEY not configured",
        )

    # 2. Fetch data from Google Places
    today = date.today()
    try:
        async with GooglePlacesWorker(settings.google_places_api_key) as worker:
            data = await worker.collect(brand.id, brand.google_place_id, today)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Failed to collect data for brand %s", brand_id)
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")

    # 3. Store menu snapshot (always, even if no menu items)
    menu_items_data = data["menu_items"]
    menu_snapshot = MenuSnapshot(
        brand_id=brand.id,
        snapshot_date=today,
        source="google_places",
        raw_data=data["raw_data"],
        item_count=len(menu_items_data),
    )
    db.add(menu_snapshot)
    await db.flush()  # get menu_snapshot.id

    # 4. Store parsed menu items
    for item_data in menu_items_data:
        menu_item = MenuItem(
            brand_id=brand.id,
            snapshot_id=menu_snapshot.id,
            item_name=item_data["item_name"],
            category=item_data.get("category"),
            price=item_data.get("price"),
            currency=item_data.get("currency", "VND"),
            description=item_data.get("description"),
            is_available=item_data.get("is_available", True),
            detected_at=today,
        )
        db.add(menu_item)

    # 5. Store hours snapshot (if hours data available)
    hours_data = data["hours_data"]
    hours_snapshot = None
    if hours_data:
        hours_snapshot = HoursSnapshot(
            brand_id=brand.id,
            snapshot_date=today,
            hours_data=hours_data,
            popular_times=data["popular_times"],
        )
        db.add(hours_snapshot)

    # 6. Collect social media data (if Apify configured)
    social_result = {}
    if settings.apify_api_token:
        from app.api.social import collect_social_for_brand
        social_result = await collect_social_for_brand(db, brand, settings.apify_api_token)

    await db.commit()

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand.id),
            "brand_name": brand.name,
            "snapshot_date": today.isoformat(),
            "menu_snapshot_id": str(menu_snapshot.id),
            "menu_items_count": len(menu_items_data),
            "hours_snapshot_id": str(hours_snapshot.id) if hours_snapshot else None,
            "has_hours_data": bool(hours_data),
            "has_popular_times": data["popular_times"] is not None,
            "rating": data["rating"],
            "user_ratings_total": data["user_ratings_total"],
            "social": social_result,
        },
    )
