"""Email Notifier — sends immediate alerts and daily digests via SendGrid.

All SendGrid calls are wrapped in try/except. Failures log the error and
set notifications.status='failed' — the pipeline never crashes.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand, BrandChange, Notification, User

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

# ── Severity badge colors ──
SEVERITY_COLORS = {"high": "#DC2626", "medium": "#F59E0B", "low": "#6B7280"}
CHANGE_TYPE_LABELS = {
    "price_increase": "漲價",
    "price_decrease": "降價",
    "new_item": "新品上架",
    "removed_item": "商品下架",
}


async def send_immediate_alert(
    db: AsyncSession,
    changes: list,
    sendgrid_api_key: str,
    from_email: str,
    owner_email: str,
    frontend_url: str,
) -> None:
    """Send immediate alert for high severity changes. Never raises."""
    high_changes = [c for c in changes if c.severity == "high"]
    if not high_changes:
        return

    for change in high_changes:
        # Skip if already notified
        if change.notified_at is not None:
            continue

        try:
            # Get brand name
            brand_result = await db.execute(
                select(Brand.name).where(Brand.id == change.brand_id)
            )
            brand_name = brand_result.scalar_one_or_none() or "Unknown"

            subject = f"【CompeteTrack 緊急】{brand_name} 發生重大變化"
            html = _build_immediate_html(change, brand_name, frontend_url)

            await _send_email(sendgrid_api_key, from_email, owner_email, subject, html)

            # Mark as notified
            change.notified_at = datetime.now(timezone.utc)

            # Get owner user_id
            user_result = await db.execute(
                select(User.id).where(User.email == owner_email)
            )
            user_id = user_result.scalar_one_or_none()

            if user_id:
                notification = Notification(
                    user_id=user_id,
                    change_ids=[change.id],
                    channel="email",
                    type="immediate",
                    status="sent",
                    subject=subject,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(notification)

            logger.info("Sent immediate alert for change %s", change.id)

        except Exception as e:
            logger.exception("Failed to send immediate alert for change %s", change.id)

            user_result = await db.execute(
                select(User.id).where(User.email == owner_email)
            )
            user_id = user_result.scalar_one_or_none()

            if user_id:
                notification = Notification(
                    user_id=user_id,
                    change_ids=[change.id],
                    channel="email",
                    type="immediate",
                    status="failed",
                    subject=f"【CompeteTrack 緊急】{brand_name} 發生重大變化",
                    error_msg=str(e)[:500],
                )
                db.add(notification)


async def send_daily_digest(
    db: AsyncSession,
    sendgrid_api_key: str,
    from_email: str,
    owner_email: str,
    frontend_url: str,
) -> dict:
    """Send daily digest of unnotified high/medium changes from last 24h.

    Returns {"status": "sent"|"failed"|"empty", "count": int}.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # Query unnotified high/medium changes
    query = (
        select(BrandChange)
        .where(
            and_(
                BrandChange.notified_at.is_(None),
                BrandChange.severity.in_(["high", "medium"]),
                BrandChange.detected_at >= cutoff,
            )
        )
        .order_by(BrandChange.detected_at.desc())
    )
    result = await db.execute(query)
    changes = list(result.scalars().all())

    today_str = datetime.now(VN_TZ).strftime("%Y-%m-%d")

    # Get owner user_id
    user_result = await db.execute(
        select(User.id).where(User.email == owner_email)
    )
    user_id = user_result.scalar_one_or_none()

    if not changes:
        # Send "no changes" email
        subject = f"【CompeteTrack】{today_str} 競品動態日報 - 0 則新動態"
        html = _build_empty_digest_html(frontend_url)

        try:
            await _send_email(sendgrid_api_key, from_email, owner_email, subject, html)

            if user_id:
                notification = Notification(
                    user_id=user_id,
                    change_ids=[],
                    channel="email",
                    type="daily_digest",
                    status="sent",
                    subject=subject,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(notification)
            return {"status": "sent", "count": 0}

        except Exception as e:
            logger.exception("Failed to send empty digest")
            if user_id:
                notification = Notification(
                    user_id=user_id,
                    change_ids=[],
                    channel="email",
                    type="daily_digest",
                    status="failed",
                    subject=subject,
                    error_msg=str(e)[:500],
                )
                db.add(notification)
            return {"status": "failed", "count": 0}

    # Build digest with changes grouped by brand
    brand_ids = list({c.brand_id for c in changes})
    brand_result = await db.execute(
        select(Brand.id, Brand.name).where(Brand.id.in_(brand_ids))
    )
    brand_names = {row[0]: row[1] for row in brand_result.fetchall()}

    subject = f"【CompeteTrack】{today_str} 競品動態日報 - {len(changes)} 則新動態"
    html = _build_digest_html(changes, brand_names, frontend_url)

    try:
        await _send_email(sendgrid_api_key, from_email, owner_email, subject, html)

        # Mark all as notified
        change_ids = []
        for change in changes:
            change.notified_at = datetime.now(timezone.utc)
            change_ids.append(change.id)

        if user_id:
            notification = Notification(
                user_id=user_id,
                change_ids=change_ids,
                channel="email",
                type="daily_digest",
                status="sent",
                subject=subject,
                sent_at=datetime.now(timezone.utc),
            )
            db.add(notification)

        logger.info("Sent daily digest with %d changes", len(changes))
        return {"status": "sent", "count": len(changes)}

    except Exception as e:
        logger.exception("Failed to send daily digest")
        if user_id:
            notification = Notification(
                user_id=user_id,
                change_ids=[c.id for c in changes],
                channel="email",
                type="daily_digest",
                status="failed",
                subject=subject,
                error_msg=str(e)[:500],
            )
            db.add(notification)
        return {"status": "failed", "count": len(changes)}


# ── SendGrid sender ──

async def _send_email(
    api_key: str, from_email: str, to_email: str, subject: str, html: str,
) -> None:
    """Send email via SendGrid HTTP API. Raises on failure."""
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email, "name": "CompeteTrack"},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
        )
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"SendGrid error {resp.status_code}: {resp.text[:200]}"
            )


# ── HTML templates ──

def _build_immediate_html(change, brand_name: str, frontend_url: str) -> str:
    change_label = CHANGE_TYPE_LABELS.get(change.change_type, change.change_type)
    color = SEVERITY_COLORS.get(change.severity, "#6B7280")
    summary = change.ai_summary or "（無 AI 摘要）"

    old_val = ""
    new_val = ""
    if change.old_value:
        old_val = str(change.old_value.get("price", change.old_value.get("item_name", "")))
    if change.new_value:
        new_val = str(change.new_value.get("price", change.new_value.get("item_name", "")))

    detected = change.detected_at
    if detected:
        detected = detected.astimezone(VN_TZ).strftime("%Y-%m-%d %H:%M")

    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1F2937;">CompeteTrack 競品警報</h2>
        <div style="background: #FEF2F2; border-left: 4px solid {color}; padding: 16px; margin: 16px 0;">
            <h3 style="margin: 0 0 8px 0;">{brand_name}</h3>
            <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                {change_label}
            </span>
        </div>
        <p><strong>AI 摘要：</strong>{summary}</p>
        <p><strong>變化：</strong>{change.field_changed} 從 {old_val} → {new_val}</p>
        <p><strong>偵測時間：</strong>{detected}（越南時間）</p>
        <a href="{frontend_url}/brands/{change.brand_id}"
           style="display: inline-block; background: #DC2626; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 6px; margin-top: 16px;">
            查看儀表板
        </a>
    </div>
    """


def _build_digest_html(
    changes: list, brand_names: dict, frontend_url: str,
) -> str:
    today = datetime.now(VN_TZ).strftime("%Y-%m-%d")

    # Group by brand
    by_brand: dict = {}
    for c in changes:
        bid = c.brand_id
        if bid not in by_brand:
            by_brand[bid] = []
        by_brand[bid].append(c)

    brand_sections = ""
    for brand_id, brand_changes in by_brand.items():
        name = brand_names.get(brand_id, "Unknown")
        items_html = ""
        for c in brand_changes:
            label = CHANGE_TYPE_LABELS.get(c.change_type, c.change_type)
            color = SEVERITY_COLORS.get(c.severity, "#6B7280")
            summary = c.ai_summary or "（無摘要）"
            items_html += f"""
            <div style="padding: 8px 0; border-bottom: 1px solid #E5E7EB;">
                <span style="background: {color}; color: white; padding: 2px 6px;
                             border-radius: 3px; font-size: 11px;">{c.severity}</span>
                <span style="margin-left: 8px; font-weight: 600;">{label}</span>
                <p style="margin: 4px 0; color: #4B5563;">{summary}</p>
            </div>
            """

        brand_sections += f"""
        <div style="margin: 16px 0; padding: 12px; background: #F9FAFB; border-radius: 8px;">
            <h3 style="margin: 0 0 8px 0;">{name}</h3>
            {items_html}
        </div>
        """

    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1F2937;">CompeteTrack 每日摘要</h2>
        <p style="color: #6B7280;">{today}・共 {len(changes)} 則競品動態</p>
        {brand_sections}
        <a href="{frontend_url}/dashboard"
           style="display: inline-block; background: #2563EB; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 6px; margin-top: 16px;">
            查看完整報告
        </a>
    </div>
    """


def _build_empty_digest_html(frontend_url: str) -> str:
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1F2937;">CompeteTrack 每日摘要</h2>
        <div style="background: #F0FDF4; border-left: 4px solid #22C55E; padding: 16px; margin: 16px 0;">
            <p style="margin: 0; color: #166534;">今日無競品異動，市場穩定。</p>
        </div>
        <a href="{frontend_url}/dashboard"
           style="display: inline-block; background: #2563EB; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 6px; margin-top: 16px;">
            查看儀表板
        </a>
    </div>
    """
