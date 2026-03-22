"""Change Detector — compares two consecutive menu snapshots and records changes.

Must be idempotent: running twice on the same snapshot pair produces no duplicates.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import MenuSnapshot, MenuItem, BrandChange, SocialSnapshot
from app.services.ai_analyzer import generate_change_summary

logger = logging.getLogger(__name__)


async def detect_changes(
    db: AsyncSession,
    brand_id: UUID,
    claude_api_key: Optional[str] = None,
    resend_api_key: Optional[str] = None,
    resend_from_email: Optional[str] = None,
    owner_email: Optional[str] = None,
    frontend_url: Optional[str] = None,
) -> list[BrandChange]:
    """Compare the two most recent snapshots for a brand and record any changes.

    Returns the list of newly created BrandChange records (empty if no changes
    or if changes were already detected for this snapshot pair).
    """
    # 1. Get the two most recent snapshots
    snapshots_query = (
        select(MenuSnapshot)
        .where(MenuSnapshot.brand_id == brand_id)
        .order_by(MenuSnapshot.snapshot_date.desc(), MenuSnapshot.created_at.desc())
        .limit(2)
    )
    result = await db.execute(snapshots_query)
    snapshots = result.scalars().all()

    if len(snapshots) < 2:
        logger.info("Brand %s has fewer than 2 snapshots — nothing to compare", brand_id)
        return []

    new_snapshot = snapshots[0]
    old_snapshot = snapshots[1]

    # 2. Get menu items for both snapshots
    old_items = await _get_items_by_snapshot(db, old_snapshot.id)
    new_items = await _get_items_by_snapshot(db, new_snapshot.id)

    # Index by item_name for comparison
    old_map = {item.item_name: item for item in old_items}
    new_map = {item.item_name: item for item in new_items}

    changes: list[BrandChange] = []

    # 3. Detect price changes (items in both snapshots)
    for name in set(old_map.keys()) & set(new_map.keys()):
        old_item = old_map[name]
        new_item = new_map[name]

        if old_item.price is not None and new_item.price is not None:
            price_change = _detect_price_change(
                brand_id, old_snapshot, new_snapshot, old_item, new_item,
            )
            if price_change:
                changes.append(price_change)

    # 4. Detect new items
    for name in set(new_map.keys()) - set(old_map.keys()):
        new_item = new_map[name]
        change = BrandChange(
            brand_id=brand_id,
            change_type="new_item",
            severity="high",
            field_changed="menu",
            old_value=None,
            new_value={
                "item_name": new_item.item_name,
                "price": float(new_item.price) if new_item.price else None,
                "category": new_item.category,
            },
            old_snapshot_id=old_snapshot.id,
            new_snapshot_id=new_snapshot.id,
        )
        changes.append(change)

    # 5. Detect removed items
    for name in set(old_map.keys()) - set(new_map.keys()):
        old_item = old_map[name]
        change = BrandChange(
            brand_id=brand_id,
            change_type="removed_item",
            severity="high",
            field_changed="menu",
            old_value={
                "item_name": old_item.item_name,
                "price": float(old_item.price) if old_item.price else None,
                "category": old_item.category,
            },
            new_value={"item_name": old_item.item_name, "removed": True},
            old_snapshot_id=old_snapshot.id,
            new_snapshot_id=new_snapshot.id,
        )
        changes.append(change)

    # 6. Filter out duplicates (idempotency)
    new_changes = []
    for change in changes:
        exists = await _change_exists(
            db, brand_id, old_snapshot.id, new_snapshot.id,
            change.field_changed, change.change_type,
            # For price changes, also match on the item name
            item_name=change.new_value.get("item_name") if change.new_value else None,
        )
        if not exists:
            new_changes.append(change)

    if not new_changes:
        logger.info("No new changes for brand %s (already detected or identical)", brand_id)
        return []

    # 7. Generate AI summaries
    for change in new_changes:
        if claude_api_key:
            try:
                summary = await generate_change_summary(change, claude_api_key)
                change.ai_summary = summary
            except Exception:
                logger.exception("AI summary failed for change %s", change.change_type)
                change.ai_summary = None
        else:
            change.ai_summary = None

    # 8. Persist
    for change in new_changes:
        db.add(change)
    await db.flush()

    # 9. Send immediate alert for high severity changes
    if resend_api_key and resend_from_email and owner_email:
        from app.services.email_notifier import send_immediate_alert
        await send_immediate_alert(
            db=db,
            changes=new_changes,
            resend_api_key=resend_api_key,
            from_email=resend_from_email,
            owner_email=owner_email,
            frontend_url=frontend_url or "",
        )

    logger.info("Detected %d new changes for brand %s", len(new_changes), brand_id)
    return new_changes


def _detect_price_change(
    brand_id: UUID,
    old_snapshot: MenuSnapshot,
    new_snapshot: MenuSnapshot,
    old_item: MenuItem,
    new_item: MenuItem,
) -> Optional[BrandChange]:
    """Create a BrandChange if price differs between old and new item."""
    old_price = Decimal(str(old_item.price))
    new_price = Decimal(str(new_item.price))

    if old_price == new_price:
        return None

    if old_price == 0:
        pct = Decimal("100")
    else:
        pct = abs((new_price - old_price) / old_price * 100)

    if pct > 10:
        severity = "high"
    elif pct >= 5:
        severity = "medium"
    else:
        severity = "low"

    change_type = "price_increase" if new_price > old_price else "price_decrease"

    return BrandChange(
        brand_id=brand_id,
        change_type=change_type,
        severity=severity,
        field_changed="price",
        old_value={
            "item_name": old_item.item_name,
            "price": float(old_price),
            "currency": old_item.currency,
        },
        new_value={
            "item_name": new_item.item_name,
            "price": float(new_price),
            "currency": new_item.currency,
            "change_pct": float(round(pct, 1)),
        },
        old_snapshot_id=old_snapshot.id,
        new_snapshot_id=new_snapshot.id,
    )


async def _get_items_by_snapshot(db: AsyncSession, snapshot_id: UUID) -> list[MenuItem]:
    result = await db.execute(
        select(MenuItem).where(MenuItem.snapshot_id == snapshot_id)
    )
    return list(result.scalars().all())


async def _change_exists(
    db: AsyncSession,
    brand_id: UUID,
    old_snapshot_id: UUID,
    new_snapshot_id: UUID,
    field_changed: str,
    change_type: str,
    item_name: Optional[str] = None,
) -> bool:
    """Check if this exact change has already been recorded (idempotency)."""
    query = select(BrandChange.id).where(
        and_(
            BrandChange.brand_id == brand_id,
            BrandChange.old_snapshot_id == old_snapshot_id,
            BrandChange.new_snapshot_id == new_snapshot_id,
            BrandChange.field_changed == field_changed,
            BrandChange.change_type == change_type,
        )
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    if not item_name:
        return len(rows) > 0

    # For item-level changes, also check the item name in new_value
    # We can't filter JSONB in the query easily, so check in Python
    for row_id in rows:
        change_result = await db.execute(
            select(BrandChange).where(BrandChange.id == row_id)
        )
        change = change_result.scalar_one_or_none()
        if change and change.new_value and change.new_value.get("item_name") == item_name:
            return True

    return False


async def detect_social_changes(
    db: AsyncSession,
    brand_id: UUID,
    platform: str,
) -> list[BrandChange]:
    """Compare two most recent social snapshots for a platform and detect changes.

    Severity thresholds:
      high:   followers increase >5% single day, OR single video views >100,000
      medium: followers change 1-5%, OR engagement_rate change >20%
      low:    any other metric change
    """
    query = (
        select(SocialSnapshot)
        .where(and_(
            SocialSnapshot.brand_id == brand_id,
            SocialSnapshot.platform == platform,
        ))
        .order_by(SocialSnapshot.snapshot_date.desc(), SocialSnapshot.created_at.desc())
        .limit(2)
    )
    result = await db.execute(query)
    snaps = result.scalars().all()

    if len(snaps) < 2:
        return []

    new_snap = snaps[0]
    old_snap = snaps[1]

    changes = []

    # Check follower change
    if old_snap.followers and new_snap.followers and old_snap.followers > 0:
        diff = new_snap.followers - old_snap.followers
        pct = abs(diff / old_snap.followers * 100)

        if diff != 0:
            if pct > 5:
                severity = "high"
            elif pct >= 1:
                severity = "medium"
            else:
                severity = "low"

            change_type = "follower_increase" if diff > 0 else "follower_decrease"
            changes.append(BrandChange(
                brand_id=brand_id,
                change_type=change_type,
                severity=severity,
                field_changed=f"{platform}_followers",
                old_value={"followers": old_snap.followers, "platform": platform},
                new_value={"followers": new_snap.followers, "platform": platform, "change_pct": round(pct, 1)},
            ))

    # Check for viral videos (TikTok/Instagram top_posts)
    if new_snap.top_posts and platform in ("tiktok", "instagram"):
        view_key = "views" if platform == "tiktok" else "likes"
        for post in new_snap.top_posts:
            views = post.get(view_key, 0)
            if views > 100000:
                changes.append(BrandChange(
                    brand_id=brand_id,
                    change_type="viral_content",
                    severity="high",
                    field_changed=f"{platform}_viral",
                    old_value=None,
                    new_value={
                        "platform": platform,
                        view_key: views,
                        "description": post.get("description", "")[:100],
                        "url": post.get("url", ""),
                    },
                ))

    # Check engagement rate change
    old_metrics = old_snap.metrics or {}
    new_metrics = new_snap.metrics or {}
    old_er = old_metrics.get("engagement_rate", 0)
    new_er = new_metrics.get("engagement_rate", 0)

    if old_er and new_er and old_er > 0:
        er_change_pct = abs((new_er - old_er) / old_er * 100)
        if er_change_pct > 20:
            changes.append(BrandChange(
                brand_id=brand_id,
                change_type="engagement_change",
                severity="medium",
                field_changed=f"{platform}_engagement",
                old_value={"engagement_rate": old_er, "platform": platform},
                new_value={"engagement_rate": new_er, "platform": platform, "change_pct": round(er_change_pct, 1)},
            ))

    # Persist (skip duplicates)
    new_changes = []
    for change in changes:
        # Simple dedup: check if same change_type + field_changed exists for today
        exists_result = await db.execute(
            select(BrandChange.id).where(and_(
                BrandChange.brand_id == brand_id,
                BrandChange.change_type == change.change_type,
                BrandChange.field_changed == change.field_changed,
                BrandChange.detected_at >= new_snap.created_at,
            )).limit(1)
        )
        if not exists_result.scalar_one_or_none():
            db.add(change)
            new_changes.append(change)

    if new_changes:
        await db.flush()
        logger.info("Detected %d social changes for brand %s (%s)", len(new_changes), brand_id, platform)

    return new_changes
