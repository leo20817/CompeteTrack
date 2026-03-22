"""Tests for email_notifier — SendGrid calls mocked."""

from datetime import date, datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.brand import Brand, MenuSnapshot, MenuItem, BrandChange, Notification, User
from app.services.email_notifier import send_immediate_alert, send_daily_digest


@pytest_asyncio.fixture
async def user_and_brand(db_session):
    """Create a user and brand for email tests."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(
        user_id=user.id, name="Phở 24", brand_type="competitor",
        google_place_id="ChIJtest",
    )
    db_session.add(brand)
    await db_session.flush()
    return user, brand


@pytest_asyncio.fixture
async def high_change(db_session, user_and_brand):
    """Create a high severity brand change."""
    user, brand = user_and_brand

    old_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 20),
        source="test", raw_data={}, item_count=1,
    )
    new_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(old_snap)
    db_session.add(new_snap)
    await db_session.flush()

    change = BrandChange(
        brand_id=brand.id,
        change_type="price_increase",
        severity="high",
        field_changed="price",
        old_value={"item_name": "Phở Bò", "price": 60000, "currency": "VND"},
        new_value={"item_name": "Phở Bò", "price": 70000, "currency": "VND", "change_pct": 16.7},
        ai_summary="Phở Bò 漲價 16.7%",
        old_snapshot_id=old_snap.id,
        new_snapshot_id=new_snap.id,
    )
    db_session.add(change)
    await db_session.flush()
    return user, brand, change


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_immediate_alert_sends_email(mock_send, db_session, high_change):
    """Immediate alert sends email for high severity and sets notified_at."""
    user, brand, change = high_change

    await send_immediate_alert(
        db=db_session,
        changes=[change],
        sendgrid_api_key="fake-key",
        from_email="test@example.com",
        owner_email=user.email,
        frontend_url="https://competetrack.zeabur.app",
    )

    mock_send.assert_called_once()
    # _send_email(api_key, from_email, to_email, subject, html) — all positional
    subject = mock_send.call_args[0][3]
    assert "CompeteTrack 緊急" in subject
    assert change.notified_at is not None


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_immediate_alert_skips_non_high(mock_send, db_session, user_and_brand):
    """Immediate alert skips medium/low severity changes."""
    user, brand = user_and_brand

    snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(snap)
    await db_session.flush()

    change = BrandChange(
        brand_id=brand.id, change_type="price_increase",
        severity="medium", field_changed="price",
        old_value={"price": 100000}, new_value={"price": 107000},
        old_snapshot_id=snap.id, new_snapshot_id=snap.id,
    )
    db_session.add(change)
    await db_session.flush()

    await send_immediate_alert(
        db=db_session, changes=[change],
        sendgrid_api_key="fake", from_email="t@t.com",
        owner_email=user.email, frontend_url="http://localhost",
    )

    mock_send.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_immediate_alert_skips_already_notified(mock_send, db_session, high_change):
    """Skips changes that already have notified_at set."""
    user, brand, change = high_change
    change.notified_at = datetime.now(timezone.utc)

    await send_immediate_alert(
        db=db_session, changes=[change],
        sendgrid_api_key="fake", from_email="t@t.com",
        owner_email=user.email, frontend_url="http://localhost",
    )

    mock_send.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock, side_effect=RuntimeError("SendGrid down"))
async def test_immediate_alert_failure_creates_failed_notification(mock_send, db_session, high_change):
    """SendGrid failure → notification with status='failed', no crash."""
    user, brand, change = high_change

    # Should not raise
    await send_immediate_alert(
        db=db_session, changes=[change],
        sendgrid_api_key="fake", from_email="t@t.com",
        owner_email=user.email, frontend_url="http://localhost",
    )

    # Check notification was created with status='failed'
    from sqlalchemy import select
    result = await db_session.execute(
        select(Notification).where(Notification.user_id == user.id)
    )
    notif = result.scalar_one_or_none()
    assert notif is not None
    assert notif.status == "failed"
    assert "SendGrid down" in notif.error_msg


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_daily_digest_with_changes(mock_send, db_session, high_change):
    """Daily digest sends email with unnotified changes."""
    user, brand, change = high_change

    result = await send_daily_digest(
        db=db_session,
        sendgrid_api_key="fake-key",
        from_email="test@example.com",
        owner_email=user.email,
        frontend_url="https://competetrack.zeabur.app",
    )

    assert result["status"] == "sent"
    assert result["count"] == 1
    mock_send.assert_called_once()
    assert change.notified_at is not None


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_daily_digest_no_changes(mock_send, db_session, user_and_brand):
    """Daily digest with 0 changes still sends 'market stable' email."""
    user, brand = user_and_brand

    result = await send_daily_digest(
        db=db_session,
        sendgrid_api_key="fake-key",
        from_email="test@example.com",
        owner_email=user.email,
        frontend_url="https://competetrack.zeabur.app",
    )

    assert result["status"] == "sent"
    assert result["count"] == 0
    mock_send.assert_called_once()
    # Subject should contain "0 則新動態"
    call_args = mock_send.call_args
    subject = call_args[0][3]
    assert "0 則新動態" in subject


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock, side_effect=RuntimeError("API error"))
async def test_daily_digest_failure(mock_send, db_session, high_change):
    """Daily digest failure → status='failed', no crash."""
    user, brand, change = high_change

    result = await send_daily_digest(
        db=db_session,
        sendgrid_api_key="fake-key",
        from_email="test@example.com",
        owner_email=user.email,
        frontend_url="https://competetrack.zeabur.app",
    )

    assert result["status"] == "failed"
    # Change should NOT be marked as notified on failure
    assert change.notified_at is None


@pytest.mark.asyncio
@patch("app.services.email_notifier._send_email", new_callable=AsyncMock)
async def test_notification_record_created(mock_send, db_session, high_change):
    """Successful email creates notification record with status='sent'."""
    user, brand, change = high_change

    await send_daily_digest(
        db=db_session,
        sendgrid_api_key="fake-key",
        from_email="test@example.com",
        owner_email=user.email,
        frontend_url="https://competetrack.zeabur.app",
    )

    from sqlalchemy import select
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.status == "sent",
        )
    )
    notif = result.scalar_one_or_none()
    assert notif is not None
    assert notif.type == "daily_digest"
    assert notif.sent_at is not None
    assert change.id in notif.change_ids
