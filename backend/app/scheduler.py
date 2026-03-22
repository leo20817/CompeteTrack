"""APScheduler jobs — daily collect + detect + digest.

Jobs run in Asia/Ho_Chi_Minh timezone:
  08:00 → collect all brands + detect changes
  08:30 → send daily digest email
"""

import logging
from datetime import timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.brand import Brand
from app.services.change_detector import detect_changes
from app.services.email_notifier import send_daily_digest
from app.workers.google_places import GooglePlacesWorker

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_collect_and_detect():
    """Collect data for all active brands and detect changes."""
    logger.info("Starting daily collect + detect job")

    async with async_session() as db:
        # Get all active brands with a google_place_id
        result = await db.execute(
            select(Brand).where(
                Brand.is_active.is_(True),
                Brand.google_place_id.isnot(None),
            )
        )
        brands = result.scalars().all()

        if not brands:
            logger.info("No active brands with google_place_id — skipping collect")
            return

        if not settings.google_places_api_key:
            logger.error("GOOGLE_PLACES_API_KEY not configured — skipping collect")
            return

        from datetime import date
        today = date.today()

        # Collect for each brand
        for brand in brands:
            try:
                async with GooglePlacesWorker(settings.google_places_api_key) as worker:
                    data = await worker.collect(brand.id, brand.google_place_id, today)

                from app.models.brand import MenuSnapshot, MenuItem, HoursSnapshot

                menu_snapshot = MenuSnapshot(
                    brand_id=brand.id,
                    snapshot_date=today,
                    source="google_places",
                    raw_data=data["raw_data"],
                    item_count=len(data["menu_items"]),
                )
                db.add(menu_snapshot)
                await db.flush()

                for item_data in data["menu_items"]:
                    db.add(MenuItem(
                        brand_id=brand.id,
                        snapshot_id=menu_snapshot.id,
                        item_name=item_data["item_name"],
                        category=item_data.get("category"),
                        price=item_data.get("price"),
                        currency=item_data.get("currency", "VND"),
                        description=item_data.get("description"),
                        is_available=item_data.get("is_available", True),
                        detected_at=today,
                    ))

                if data["hours_data"]:
                    db.add(HoursSnapshot(
                        brand_id=brand.id,
                        snapshot_date=today,
                        hours_data=data["hours_data"],
                        popular_times=data["popular_times"],
                    ))

                await db.commit()
                logger.info("Collected data for brand %s (%s)", brand.name, brand.id)

            except Exception:
                logger.exception("Failed to collect for brand %s", brand.name)
                await db.rollback()

        # Detect changes for each brand
        for brand in brands:
            try:
                async with async_session() as detect_db:
                    await detect_changes(
                        detect_db,
                        brand.id,
                        claude_api_key=settings.claude_api_key,
                    )
                    await detect_db.commit()
            except Exception:
                logger.exception("Failed to detect changes for brand %s", brand.name)

    logger.info("Daily collect + detect complete")


async def daily_digest():
    """Send daily digest email with unnotified changes."""
    logger.info("Starting daily digest job")

    if not settings.resend_api_key or not settings.resend_from_email:
        logger.error("Resend not configured — skipping digest")
        return

    async with async_session() as db:
        result = await send_daily_digest(
            db=db,
            resend_api_key=settings.resend_api_key,
            from_email=settings.resend_from_email,
            owner_email=settings.owner_user_email,
            frontend_url=settings.frontend_url,
        )
        await db.commit()

    logger.info("Daily digest result: %s", result)


async def daily_social_collect():
    """Collect social media data for all active brands."""
    logger.info("Starting daily social collect job")

    if not settings.apify_api_token:
        logger.error("APIFY_API_TOKEN not configured — skipping social collect")
        return

    async with async_session() as db:
        result = await db.execute(
            select(Brand).where(Brand.is_active.is_(True))
        )
        brands = result.scalars().all()

        for brand in brands:
            has_social = brand.tiktok_username or brand.instagram_username or brand.facebook_url
            if not has_social:
                continue

            try:
                from app.api.social import collect_social_for_brand
                await collect_social_for_brand(db, brand, settings.apify_api_token)
                await db.commit()
                logger.info("Social collected for %s", brand.name)
            except Exception:
                logger.exception("Social collect failed for %s", brand.name)
                await db.rollback()

    logger.info("Daily social collect complete")


def start_scheduler():
    """Register and start APScheduler jobs."""
    tz = settings.timezone

    scheduler.add_job(
        daily_collect_and_detect,
        CronTrigger(
            hour=settings.collect_hour,
            minute=settings.collect_minute,
            timezone=tz,
        ),
        id="daily_collect",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_social_collect,
        CronTrigger(hour=9, minute=0, timezone=tz),
        id="daily_social",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_digest,
        CronTrigger(
            hour=settings.digest_email_hour,
            minute=settings.digest_email_minute,
            timezone=tz,
        ),
        id="daily_digest",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — collect at %02d:%02d, social at 09:00, digest at %02d:%02d (%s)",
        settings.collect_hour, settings.collect_minute,
        settings.digest_email_hour, settings.digest_email_minute,
        tz,
    )
