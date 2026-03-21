"""Tests for GET /api/menu endpoints."""

from datetime import date
from uuid import uuid4

import pytest

from app.models.brand import MenuSnapshot, MenuItem


@pytest.mark.asyncio
async def test_get_menu_no_snapshots(client, sample_brand):
    """GET menu returns empty when no snapshots exist."""
    resp = await client.get(f"/api/menu/{sample_brand.id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["snapshot"] is None
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_get_menu_with_items(client, db_session, sample_brand):
    """GET menu returns items from the latest snapshot."""
    snapshot = MenuSnapshot(
        brand_id=sample_brand.id,
        snapshot_date=date(2026, 3, 21),
        source="google_places",
        raw_data={"status": "OK"},
        item_count=2,
    )
    db_session.add(snapshot)
    await db_session.flush()

    items = [
        MenuItem(
            brand_id=sample_brand.id,
            snapshot_id=snapshot.id,
            item_name="Phở Bò",
            category="Phở",
            price=65000,
            currency="VND",
            is_available=True,
            detected_at=date(2026, 3, 21),
        ),
        MenuItem(
            brand_id=sample_brand.id,
            snapshot_id=snapshot.id,
            item_name="Phở Gà",
            category="Phở",
            price=60000,
            currency="VND",
            is_available=True,
            detected_at=date(2026, 3, 21),
        ),
    ]
    for item in items:
        db_session.add(item)
    await db_session.commit()

    resp = await client.get(f"/api/menu/{sample_brand.id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["total"] == 2
    assert data["data"]["snapshot"]["source"] == "google_places"
    names = {i["item_name"] for i in data["data"]["items"]}
    assert "Phở Bò" in names
    assert "Phở Gà" in names


@pytest.mark.asyncio
async def test_get_menu_returns_latest_snapshot(client, db_session, sample_brand):
    """GET menu returns items from the MOST RECENT snapshot only."""
    # Old snapshot
    old = MenuSnapshot(
        brand_id=sample_brand.id,
        snapshot_date=date(2026, 3, 20),
        source="google_places",
        raw_data={"status": "OK"},
        item_count=1,
    )
    db_session.add(old)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=sample_brand.id,
        snapshot_id=old.id,
        item_name="Old Item",
        price=50000,
        currency="VND",
        is_available=True,
        detected_at=date(2026, 3, 20),
    ))

    # New snapshot
    new = MenuSnapshot(
        brand_id=sample_brand.id,
        snapshot_date=date(2026, 3, 21),
        source="google_places",
        raw_data={"status": "OK"},
        item_count=1,
    )
    db_session.add(new)
    await db_session.flush()
    db_session.add(MenuItem(
        brand_id=sample_brand.id,
        snapshot_id=new.id,
        item_name="New Item",
        price=70000,
        currency="VND",
        is_available=True,
        detected_at=date(2026, 3, 21),
    ))
    await db_session.commit()

    resp = await client.get(f"/api/menu/{sample_brand.id}")

    data = resp.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["item_name"] == "New Item"


@pytest.mark.asyncio
async def test_get_menu_brand_not_found(client):
    """GET menu returns 404 for non-existent brand."""
    resp = await client.get(f"/api/menu/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_snapshots(client, db_session, sample_brand):
    """GET /api/menu/{id}/snapshots returns all snapshots."""
    for i in range(3):
        db_session.add(MenuSnapshot(
            brand_id=sample_brand.id,
            snapshot_date=date(2026, 3, 19 + i),
            source="google_places",
            raw_data={"day": i},
            item_count=0,
        ))
    await db_session.commit()

    resp = await client.get(f"/api/menu/{sample_brand.id}/snapshots")

    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["items"]) == 3


@pytest.mark.asyncio
async def test_list_snapshots_brand_not_found(client):
    """GET snapshots returns 404 for non-existent brand."""
    resp = await client.get(f"/api/menu/{uuid4()}/snapshots")
    assert resp.status_code == 404
