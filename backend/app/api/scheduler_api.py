import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.response import APIResponse
from app.services.email_notifier import send_daily_digest
from app.scheduler import scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status and next run times."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return APIResponse(
        success=True,
        data={
            "running": scheduler.running,
            "jobs": jobs,
        },
    )


@router.post("/run-daily-digest")
async def run_daily_digest(db: AsyncSession = Depends(get_db)):
    """Manually trigger daily digest email."""
    if not settings.resend_api_key or not settings.resend_from_email:
        return APIResponse(
            success=False,
            error="Resend not configured (RESEND_API_KEY or RESEND_FROM_EMAIL missing)",
        )

    result = await send_daily_digest(
        db=db,
        resend_api_key=settings.resend_api_key,
        from_email=settings.resend_from_email,
        owner_email=settings.owner_user_email,
        frontend_url=settings.frontend_url,
    )
    await db.commit()

    return APIResponse(success=True, data=result)


@router.post("/run-now")
async def run_now():
    """Manually trigger full collect + detect for all brands."""
    from app.scheduler import daily_collect_and_detect

    try:
        await daily_collect_and_detect()
        return APIResponse(success=True, data={"message": "收集完成"})
    except Exception as e:
        logger.exception("Manual run-now failed")
        return APIResponse(success=False, error=str(e))
