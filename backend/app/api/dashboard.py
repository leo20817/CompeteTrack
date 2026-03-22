from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brand import Brand, BrandChange, MenuSnapshot
from app.schemas.response import APIResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Overview stats for the dashboard."""
    # Total active brands
    brand_count = (await db.execute(
        select(func.count()).select_from(Brand).where(Brand.is_active.is_(True))
    )).scalar() or 0

    # Changes this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    week_changes = (await db.execute(
        select(func.count()).select_from(BrandChange).where(
            BrandChange.detected_at >= week_ago
        )
    )).scalar() or 0

    # Unnotified changes
    unnotified = (await db.execute(
        select(func.count()).select_from(BrandChange).where(
            BrandChange.notified_at.is_(None)
        )
    )).scalar() or 0

    # Last snapshot time
    last_snapshot = (await db.execute(
        select(MenuSnapshot.created_at)
        .order_by(MenuSnapshot.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    return APIResponse(
        success=True,
        data={
            "brand_count": brand_count,
            "week_changes": week_changes,
            "unnotified": unnotified,
            "last_updated": last_snapshot.isoformat() if last_snapshot else None,
        },
    )


@router.get("/timeline")
async def get_change_timeline(
    days: int = Query(default=30, le=90),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Change timeline for the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(BrandChange)
        .where(BrandChange.detected_at >= cutoff)
        .order_by(BrandChange.detected_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    changes = result.scalars().all()

    # Get brand names
    brand_ids = list({c.brand_id for c in changes})
    brand_names = {}
    if brand_ids:
        brand_result = await db.execute(
            select(Brand.id, Brand.name).where(Brand.id.in_(brand_ids))
        )
        brand_names = {row[0]: row[1] for row in brand_result.fetchall()}

    items = []
    for c in changes:
        items.append({
            "id": str(c.id),
            "brand_id": str(c.brand_id),
            "brand_name": brand_names.get(c.brand_id, "Unknown"),
            "change_type": c.change_type,
            "severity": c.severity,
            "field_changed": c.field_changed,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "ai_summary": c.ai_summary,
            "detected_at": c.detected_at.isoformat() if c.detected_at else None,
        })

    return APIResponse(success=True, data={"items": items, "total": len(items)})
