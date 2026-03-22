"""Menu photo upload and AI parsing endpoints."""

import base64
import logging
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.brand import Brand, MenuSnapshot, MenuItem
from app.schemas.response import APIResponse
from app.services.menu_vision import parse_menu_from_base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/menu-upload", tags=["menu-upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file


async def _upload_to_supabase(
    file_data: bytes,
    filename: str,
    content_type: str,
    brand_id: str,
) -> Optional[str]:
    """Upload file to Supabase Storage, return public URL."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase Storage not configured — storing as base64 only")
        return None

    path = f"menu-photos/{brand_id}/{uuid4().hex[:8]}_{filename}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.supabase_url}/storage/v1/object/menu-photos/{path}",
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "Content-Type": content_type,
            },
            content=file_data,
        )

        if resp.status_code in (200, 201):
            return f"{settings.supabase_url}/storage/v1/object/public/menu-photos/{path}"
        else:
            logger.error("Supabase upload failed: %s %s", resp.status_code, resp.text[:200])
            return None


@router.post("/{brand_id}/upload")
async def upload_menu_photos(
    brand_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload menu photos and parse with Claude Vision.

    Returns parsed menu items for user review (not yet saved to DB).
    """
    # Validate brand
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if not settings.openrouter_api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 photos per upload")

    # Process files
    images_b64 = []
    photo_urls = []

    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {f.content_type}. Use JPG, PNG, or WebP.",
            )

        data = await f.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {f.filename} exceeds 10MB limit")

        # Upload to Supabase Storage
        url = await _upload_to_supabase(data, f.filename or "photo.jpg", f.content_type, str(brand_id))
        if url:
            photo_urls.append(url)

        # Prepare base64 for Claude Vision
        images_b64.append({
            "data": base64.b64encode(data).decode("utf-8"),
            "media_type": f.content_type,
        })

    # Parse with Claude Vision
    parsed = await parse_menu_from_base64(images_b64, settings.openrouter_api_key)

    return APIResponse(
        success=True,
        data={
            "brand_id": str(brand_id),
            "brand_name": brand.name,
            "photo_count": len(files),
            "photo_urls": photo_urls,
            "parsed": parsed,
        },
    )


@router.post("/{brand_id}/confirm")
async def confirm_menu_items(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
    items: list[dict] = [],
    photo_urls: list[str] = [],
):
    """Confirm parsed menu items and save to DB.

    Called after user reviews AI-parsed results.
    """
    brand_result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    today = date.today()

    # Create snapshot
    snapshot = MenuSnapshot(
        brand_id=brand.id,
        snapshot_date=today,
        source="manual_photo",
        raw_data={
            "photo_urls": photo_urls,
            "ai_parsed": True,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        },
        item_count=len(items),
    )
    db.add(snapshot)
    await db.flush()

    # Create menu items
    for item_data in items:
        item = MenuItem(
            brand_id=brand.id,
            snapshot_id=snapshot.id,
            item_name=item_data.get("item_name", ""),
            category=item_data.get("category"),
            price=item_data.get("price"),
            currency=item_data.get("currency", "VND"),
            description=item_data.get("description"),
            is_available=True,
            detected_at=today,
        )
        db.add(item)

    await db.commit()

    return APIResponse(
        success=True,
        data={
            "snapshot_id": str(snapshot.id),
            "items_saved": len(items),
            "snapshot_date": today.isoformat(),
        },
    )
