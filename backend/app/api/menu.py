from typing import Optional
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


@router.get("/{brand_id}/diff")
async def get_menu_diff(
    brand_id: UUID,
    old_snapshot_id: Optional[UUID] = Query(default=None),
    new_snapshot_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Compare two snapshots and return diff (added/removed/price_changed items)."""
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    if not brand_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Brand not found")

    # If no snapshot IDs provided, use the two most recent
    if not old_snapshot_id or not new_snapshot_id:
        snap_query = (
            select(MenuSnapshot)
            .where(MenuSnapshot.brand_id == brand_id)
            .order_by(MenuSnapshot.snapshot_date.desc(), MenuSnapshot.created_at.desc())
            .limit(2)
        )
        snap_result = await db.execute(snap_query)
        snaps = snap_result.scalars().all()
        if len(snaps) < 2:
            return APIResponse(
                success=True,
                data={"diff": [], "message": "Need at least 2 snapshots to compare"},
            )
        new_snapshot_id = snaps[0].id
        old_snapshot_id = snaps[1].id

    # Get items for both snapshots
    old_items_result = await db.execute(
        select(MenuItem).where(MenuItem.snapshot_id == old_snapshot_id)
    )
    new_items_result = await db.execute(
        select(MenuItem).where(MenuItem.snapshot_id == new_snapshot_id)
    )

    old_items = {i.item_name: i for i in old_items_result.scalars().all()}
    new_items = {i.item_name: i for i in new_items_result.scalars().all()}

    diff = []

    # Items in both
    for name in set(old_items.keys()) & set(new_items.keys()):
        old_i = old_items[name]
        new_i = new_items[name]
        status = "unchanged"
        if old_i.price and new_i.price and old_i.price != new_i.price:
            status = "price_changed"
        diff.append({
            "item_name": name,
            "category": new_i.category,
            "status": status,
            "old_price": float(old_i.price) if old_i.price else None,
            "new_price": float(new_i.price) if new_i.price else None,
            "currency": new_i.currency,
        })

    # New items
    for name in set(new_items.keys()) - set(old_items.keys()):
        i = new_items[name]
        diff.append({
            "item_name": name,
            "category": i.category,
            "status": "added",
            "old_price": None,
            "new_price": float(i.price) if i.price else None,
            "currency": i.currency,
        })

    # Removed items
    for name in set(old_items.keys()) - set(new_items.keys()):
        i = old_items[name]
        diff.append({
            "item_name": name,
            "category": i.category,
            "status": "removed",
            "old_price": float(i.price) if i.price else None,
            "new_price": None,
            "currency": i.currency,
        })

    diff.sort(key=lambda x: ({"removed": 0, "added": 1, "price_changed": 2, "unchanged": 3}[x["status"]], x["item_name"]))

    return APIResponse(
        success=True,
        data={
            "old_snapshot_id": str(old_snapshot_id),
            "new_snapshot_id": str(new_snapshot_id),
            "diff": diff,
            "total": len(diff),
        },
    )
