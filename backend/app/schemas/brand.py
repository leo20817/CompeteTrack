from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    brand_type: str = "competitor"
    aliases: list[str] = []
    google_place_id: Optional[str] = None
    website_url: Optional[str] = None
    foody_url: Optional[str] = None
    notes: Optional[str] = None


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    brand_type: Optional[str] = None
    aliases: Optional[list[str]] = None
    google_place_id: Optional[str] = None
    website_url: Optional[str] = None
    foody_url: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class BrandOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    aliases: list[str]
    brand_type: str
    google_place_id: Optional[str]
    website_url: Optional[str]
    foody_url: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
