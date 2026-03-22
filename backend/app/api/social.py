import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.brand import Brand, SocialSnapshot
from app.schemas.response import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/{brand_id}")
async def get_social_data(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get latest social snapshots for all 3 platforms."""
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    result = {}
    for platform in ["tiktok", "instagram", "facebook"]:
        query = (
            select(SocialSnapshot)
            .where(and_(
                SocialSnapshot.brand_id == brand_id,
                SocialSnapshot.platform == platform,
            ))
            .order_by(SocialSnapshot.snapshot_date.desc(), SocialSnapshot.created_at.desc())
            .limit(1)
        )
        snap_result = await db.execute(query)
        snap = snap_result.scalar_one_or_none()

        if snap:
            result[platform] = {
                "snapshot_date": snap.snapshot_date.isoformat(),
                "followers": snap.followers,
                "following": snap.following,
                "total_posts": snap.total_posts,
                "metrics": snap.metrics,
                "top_posts": snap.top_posts,
            }
        else:
            result[platform] = None

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand_id),
            "brand_name": brand.name,
            "tiktok_username": brand.tiktok_username,
            "instagram_username": brand.instagram_username,
            "facebook_url": brand.facebook_url,
            **result,
        },
    )


async def collect_social_for_brand(db: AsyncSession, brand: Brand, api_token: str) -> dict:
    """Collect social data for a single brand across all platforms.

    Called from collect.py and scheduler.py. Never raises — logs and continues.
    """
    today = date.today()
    collected = {}

    # TikTok
    if brand.tiktok_username:
        try:
            from app.workers.apify_tiktok import collect_tiktok
            data = await collect_tiktok(brand.tiktok_username, brand.id, api_token, today)
            snap = SocialSnapshot(
                brand_id=brand.id,
                platform="tiktok",
                snapshot_date=today,
                followers=data["followers"],
                following=data["following"],
                total_posts=data["total_posts"],
                metrics=data["metrics"],
                top_posts=data["top_posts"],
            )
            db.add(snap)
            collected["tiktok"] = True
            logger.info("Collected TikTok for %s (@%s)", brand.name, brand.tiktok_username)
        except Exception:
            logger.exception("TikTok collection failed for %s", brand.name)
            collected["tiktok"] = False
    else:
        logger.info("Skipping TikTok for %s — no username set", brand.name)

    # Instagram
    if brand.instagram_username:
        try:
            from app.workers.apify_instagram import collect_instagram
            data = await collect_instagram(brand.instagram_username, brand.id, api_token, today)
            snap = SocialSnapshot(
                brand_id=brand.id,
                platform="instagram",
                snapshot_date=today,
                followers=data["followers"],
                following=data["following"],
                total_posts=data["total_posts"],
                metrics=data["metrics"],
                top_posts=data["top_posts"],
            )
            db.add(snap)
            collected["instagram"] = True
            logger.info("Collected Instagram for %s (@%s)", brand.name, brand.instagram_username)
        except Exception:
            logger.exception("Instagram collection failed for %s", brand.name)
            collected["instagram"] = False
    else:
        logger.info("Skipping Instagram for %s — no username set", brand.name)

    # Facebook
    if brand.facebook_url:
        try:
            from app.workers.apify_facebook import collect_facebook
            data = await collect_facebook(brand.facebook_url, brand.id, api_token, today)
            snap = SocialSnapshot(
                brand_id=brand.id,
                platform="facebook",
                snapshot_date=today,
                followers=data["followers"],
                following=data["following"],
                total_posts=data["total_posts"],
                metrics=data["metrics"],
                top_posts=data["top_posts"],
            )
            db.add(snap)
            collected["facebook"] = True
            logger.info("Collected Facebook for %s (%s)", brand.name, brand.facebook_url)
        except Exception:
            logger.exception("Facebook collection failed for %s", brand.name)
            collected["facebook"] = False
    else:
        logger.info("Skipping Facebook for %s — no URL set", brand.name)

    return collected
