from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brand import Brand, MenuSnapshot, MenuItem
from app.schemas.menu import MenuItemOut, MenuSnapshotOut
from app.schemas.response import APIResponse

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("/{brand_id}")
async def get_latest_menu(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the latest menu items for a brand (from the most recent snapshot)."""

    # Verify brand exists
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get latest snapshot
    snapshot_query = (
        select(MenuSnapshot)
        .where(MenuSnapshot.brand_id == brand_id)
        .order_by(MenuSnapshot.snapshot_date.desc(), MenuSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot_result = await db.execute(snapshot_query)
    snapshot = snapshot_result.scalar_one_or_none()

    if not snapshot:
        return APIResponse(
            success=True,
            data={
                "brand_id": str(brand_id),
                "brand_name": brand.name,
                "snapshot": None,
                "items": [],
                "total": 0,
            },
        )

    # Get menu items for this snapshot
    items_query = (
        select(MenuItem)
        .where(MenuItem.snapshot_id == snapshot.id)
        .order_by(MenuItem.category, MenuItem.item_name)
    )
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand_id),
            "brand_name": brand.name,
            "snapshot": MenuSnapshotOut.model_validate(snapshot).model_dump(mode="json"),
            "items": [MenuItemOut.model_validate(i).model_dump(mode="json") for i in items],
            "total": len(items),
        },
    )


@router.get("/{brand_id}/snapshots")
async def list_menu_snapshots(
    brand_id: UUID,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all menu snapshots for a brand."""

    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    if not brand_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Brand not found")

    query = (
        select(MenuSnapshot)
        .where(MenuSnapshot.brand_id == brand_id)
        .order_by(MenuSnapshot.snapshot_date.desc(), MenuSnapshot.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    snapshots = result.scalars().all()

    count_query = select(func.count()).select_from(MenuSnapshot).where(
        MenuSnapshot.brand_id == brand_id
    )
    total = (await db.execute(count_query)).scalar()

    return APIResponse(
        success=True,
        data={
            "items": [MenuSnapshotOut.model_validate(s).model_dump(mode="json") for s in snapshots],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )
