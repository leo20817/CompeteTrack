from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.brand import HoursSnapshot, Brand
from app.schemas.response import APIResponse

router = APIRouter(prefix="/api/hours", tags=["hours"])


@router.get("/{brand_id}")
async def get_latest_hours(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the latest hours snapshot for a brand."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    hours_result = await db.execute(
        select(HoursSnapshot)
        .where(HoursSnapshot.brand_id == brand_id)
        .order_by(HoursSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot = hours_result.scalar_one_or_none()

    if not snapshot:
        return APIResponse(
            success=True,
            data={
                "brand_id": str(brand_id),
                "brand_name": brand.name,
                "snapshot": None,
                "hours": None,
                "popular_times": None,
            },
        )

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand_id),
            "brand_name": brand.name,
            "snapshot": {
                "id": str(snapshot.id),
                "snapshot_date": str(snapshot.snapshot_date),
                "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
            },
            "hours": snapshot.hours_data,
            "popular_times": snapshot.popular_times,
        },
    )
