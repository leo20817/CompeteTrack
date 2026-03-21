from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.brand import Brand, User
from app.schemas.brand import BrandCreate, BrandUpdate, BrandOut
from app.schemas.response import APIResponse

router = APIRouter(prefix="/api/brands", tags=["brands"])


async def get_owner_user(db: AsyncSession) -> User:
    """Get the MVP owner user, creating one if it doesn't exist."""
    result = await db.execute(select(User).where(User.plan == "owner").limit(1))
    user = result.scalar_one_or_none()
    if not user:
        from app.config import settings
        user = User(email=settings.owner_user_email, plan="owner", brand_limit=999)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@router.get("")
async def list_brands(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    user = await get_owner_user(db)
    query = (
        select(Brand)
        .where(Brand.user_id == user.id, Brand.is_active.is_(True))
        .order_by(Brand.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    brands = result.scalars().all()

    count_query = select(func.count()).select_from(Brand).where(
        Brand.user_id == user.id, Brand.is_active.is_(True)
    )
    total = (await db.execute(count_query)).scalar()

    return APIResponse(
        success=True,
        data={
            "items": [BrandOut.model_validate(b).model_dump(mode="json") for b in brands],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


@router.post("")
async def create_brand(
    brand_in: BrandCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await get_owner_user(db)
    brand = Brand(
        user_id=user.id,
        name=brand_in.name,
        aliases=brand_in.aliases,
        brand_type=brand_in.brand_type,
        google_place_id=brand_in.google_place_id,
        website_url=brand_in.website_url,
        foody_url=brand_in.foody_url,
        notes=brand_in.notes,
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return APIResponse(
        success=True,
        data=BrandOut.model_validate(brand).model_dump(mode="json"),
    )


@router.get("/{brand_id}")
async def get_brand(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return APIResponse(
        success=True,
        data=BrandOut.model_validate(brand).model_dump(mode="json"),
    )


@router.put("/{brand_id}")
async def update_brand(
    brand_id: UUID,
    brand_in: BrandUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = brand_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    await db.commit()
    await db.refresh(brand)
    return APIResponse(
        success=True,
        data=BrandOut.model_validate(brand).model_dump(mode="json"),
    )


@router.delete("/{brand_id}")
async def delete_brand(brand_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    brand.is_active = False
    await db.commit()
    return APIResponse(success=True, data={"id": str(brand_id), "is_active": False})
