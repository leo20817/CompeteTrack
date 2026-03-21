"""Tests for change_detector service — all AI calls mocked."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from app.models.brand import Brand, MenuSnapshot, MenuItem, BrandChange, User
from app.services.change_detector import detect_changes


@pytest_asyncio.fixture
async def brand_with_snapshots(db_session):
    """Create a brand with two snapshots that have a >10% price difference."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(
        user_id=user.id,
        name="Test Phở",
        brand_type="competitor",
        google_place_id="ChIJtest",
    )
    db_session.add(brand)
    await db_session.flush()

    # Old snapshot — Phở Bò costs 60,000
    old_snap = MenuSnapshot(
        brand_id=brand.id,
        snapshot_date=date(2026, 3, 20),
        source="google_places",
        raw_data={"status": "OK"},
        item_count=2,
    )
    db_session.add(old_snap)
    await db_session.flush()

    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Phở Bò", category="Phở", price=60000,
        currency="VND", is_available=True, detected_at=date(2026, 3, 20),
    ))
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Gỏi Cuốn", category="Khai Vị", price=35000,
        currency="VND", is_available=True, detected_at=date(2026, 3, 20),
    ))

    # New snapshot — Phở Bò costs 70,000 (16.7% increase → high severity)
    new_snap = MenuSnapshot(
        brand_id=brand.id,
        snapshot_date=date(2026, 3, 21),
        source="google_places",
        raw_data={"status": "OK"},
        item_count=2,
    )
    db_session.add(new_snap)
    await db_session.flush()

    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Phở Bò", category="Phở", price=70000,
        currency="VND", is_available=True, detected_at=date(2026, 3, 21),
    ))
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Gỏi Cuốn", category="Khai Vị", price=35000,
        currency="VND", is_available=True, detected_at=date(2026, 3, 21),
    ))

    await db_session.flush()
    return brand, old_snap, new_snap


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value="測試摘要")
async def test_detect_price_increase_high(mock_ai, db_session, brand_with_snapshots):
    """Detects >10% price increase as high severity."""
    brand, old_snap, new_snap = brand_with_snapshots

    changes = await detect_changes(db_session, brand.id, claude_api_key="fake-key")

    assert len(changes) == 1
    c = changes[0]
    assert c.change_type == "price_increase"
    assert c.severity == "high"
    assert c.field_changed == "price"
    assert c.old_value["price"] == 60000.0
    assert c.new_value["price"] == 70000.0
    assert c.new_value["change_pct"] == 16.7
    assert c.old_snapshot_id == old_snap.id
    assert c.new_snapshot_id == new_snap.id
    assert c.ai_summary == "測試摘要"


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value="測試摘要")
async def test_idempotency(mock_ai, db_session, brand_with_snapshots):
    """Running detect_changes twice produces no duplicate changes."""
    brand, _, _ = brand_with_snapshots

    changes_1 = await detect_changes(db_session, brand.id, claude_api_key="fake-key")
    assert len(changes_1) == 1

    changes_2 = await detect_changes(db_session, brand.id, claude_api_key="fake-key")
    assert len(changes_2) == 0  # no new changes


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value=None)
async def test_detect_new_item(mock_ai, db_session):
    """Detects a new menu item as high severity."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(user_id=user.id, name="Test", brand_type="competitor")
    db_session.add(brand)
    await db_session.flush()

    old_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 20),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(old_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Phở Bò", price=60000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 20),
    ))

    new_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=2,
    )
    db_session.add(new_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Phở Bò", price=60000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 21),
    ))
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Bún Bò Huế", price=75000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 21),
    ))
    await db_session.flush()

    changes = await detect_changes(db_session, brand.id)
    new_item_changes = [c for c in changes if c.change_type == "new_item"]
    assert len(new_item_changes) == 1
    assert new_item_changes[0].new_value["item_name"] == "Bún Bò Huế"
    assert new_item_changes[0].severity == "high"


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value=None)
async def test_detect_removed_item(mock_ai, db_session):
    """Detects a removed menu item as high severity."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(user_id=user.id, name="Test", brand_type="competitor")
    db_session.add(brand)
    await db_session.flush()

    old_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 20),
        source="test", raw_data={}, item_count=2,
    )
    db_session.add(old_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Phở Bò", price=60000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 20),
    ))
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Cơm Tấm", price=45000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 20),
    ))

    new_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(new_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Phở Bò", price=60000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 21),
    ))
    await db_session.flush()

    changes = await detect_changes(db_session, brand.id)
    removed = [c for c in changes if c.change_type == "removed_item"]
    assert len(removed) == 1
    assert removed[0].old_value["item_name"] == "Cơm Tấm"
    assert removed[0].severity == "high"


@pytest.mark.asyncio
async def test_detect_no_changes_with_one_snapshot(db_session):
    """Returns empty when brand has only one snapshot."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(user_id=user.id, name="Test", brand_type="competitor")
    db_session.add(brand)
    await db_session.flush()

    snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(snap)
    await db_session.flush()

    changes = await detect_changes(db_session, brand.id)
    assert changes == []


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value=None)
async def test_detect_medium_severity(mock_ai, db_session):
    """5-10% price change → medium severity."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(user_id=user.id, name="Test", brand_type="competitor")
    db_session.add(brand)
    await db_session.flush()

    old_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 20),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(old_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Phở Bò", price=100000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 20),
    ))

    new_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(new_snap)
    await db_session.flush()
    # 7% increase → medium
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Phở Bò", price=107000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 21),
    ))
    await db_session.flush()

    changes = await detect_changes(db_session, brand.id)
    assert len(changes) == 1
    assert changes[0].severity == "medium"


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value=None)
async def test_detect_low_severity(mock_ai, db_session):
    """<5% price change → low severity."""
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()

    brand = Brand(user_id=user.id, name="Test", brand_type="competitor")
    db_session.add(brand)
    await db_session.flush()

    old_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 20),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(old_snap)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=old_snap.id,
        item_name="Phở Bò", price=100000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 20),
    ))

    new_snap = MenuSnapshot(
        brand_id=brand.id, snapshot_date=date(2026, 3, 21),
        source="test", raw_data={}, item_count=1,
    )
    db_session.add(new_snap)
    await db_session.flush()
    # 3% decrease → low
    db_session.add(MenuItem(
        brand_id=brand.id, snapshot_id=new_snap.id,
        item_name="Phở Bò", price=97000, currency="VND",
        is_available=True, detected_at=date(2026, 3, 21),
    ))
    await db_session.flush()

    changes = await detect_changes(db_session, brand.id)
    assert len(changes) == 1
    assert changes[0].severity == "low"
    assert changes[0].change_type == "price_decrease"


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, side_effect=Exception("API error"))
async def test_ai_failure_does_not_crash(mock_ai, db_session, brand_with_snapshots):
    """AI summary failure → ai_summary=None, no crash."""
    brand, _, _ = brand_with_snapshots

    changes = await detect_changes(db_session, brand.id, claude_api_key="fake-key")
    assert len(changes) == 1
    assert changes[0].ai_summary is None


@pytest.mark.asyncio
@patch("app.services.change_detector.generate_change_summary", new_callable=AsyncMock, return_value=None)
async def test_no_ai_key_sets_null_summary(mock_ai, db_session, brand_with_snapshots):
    """No claude_api_key → ai_summary=None, no API call."""
    brand, _, _ = brand_with_snapshots

    changes = await detect_changes(db_session, brand.id, claude_api_key=None)
    assert len(changes) == 1
    assert changes[0].ai_summary is None
    mock_ai.assert_not_called()
