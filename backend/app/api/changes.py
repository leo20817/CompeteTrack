import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.brand import Brand, BrandChange
from app.schemas.change import BrandChangeOut
from app.schemas.response import APIResponse
from app.services.change_detector import detect_changes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/changes", tags=["changes"])


@router.get("")
async def list_changes(
    brand_id: Optional[UUID] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List brand changes with optional filters."""
    query = select(BrandChange).order_by(BrandChange.detected_at.desc())
    count_query = select(func.count()).select_from(BrandChange)

    if brand_id:
        query = query.where(BrandChange.brand_id == brand_id)
        count_query = count_query.where(BrandChange.brand_id == brand_id)
    if severity:
        query = query.where(BrandChange.severity == severity)
        count_query = count_query.where(BrandChange.severity == severity)

    total = (await db.execute(count_query)).scalar()

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    changes = result.scalars().all()

    return APIResponse(
        success=True,
        data={
            "items": [BrandChangeOut.model_validate(c).model_dump(mode="json") for c in changes],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


@router.get("/unnotified")
async def list_unnotified_changes(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List changes that have not been notified yet."""
    query = (
        select(BrandChange)
        .where(BrandChange.notified_at.is_(None))
        .order_by(BrandChange.detected_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    changes = result.scalars().all()

    return APIResponse(
        success=True,
        data={
            "items": [BrandChangeOut.model_validate(c).model_dump(mode="json") for c in changes],
            "total": len(changes),
        },
    )


@router.patch("/{change_id}/read")
async def mark_change_read(change_id: UUID, db: AsyncSession = Depends(get_db)):
    """Mark a change as notified (sets notified_at)."""
    result = await db.execute(select(BrandChange).where(BrandChange.id == change_id))
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    change.notified_at = datetime.now(timezone.utc)
    await db.commit()

    return APIResponse(
        success=True,
        data=BrandChangeOut.model_validate(change).model_dump(mode="json"),
    )


@router.post("/detect/{brand_id}")
async def trigger_detect_changes(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually trigger change detection for a brand."""
    # Verify brand exists
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    new_changes = await detect_changes(
        db, brand_id,
        claude_api_key=settings.claude_api_key,
        sendgrid_api_key=settings.sendgrid_api_key,
        sendgrid_from_email=settings.sendgrid_from_email,
        owner_email=settings.owner_user_email,
        frontend_url=settings.frontend_url,
    )
    await db.commit()

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand_id),
            "new_changes_count": len(new_changes),
            "changes": [
                BrandChangeOut.model_validate(c).model_dump(mode="json")
                for c in new_changes
            ],
        },
    )
