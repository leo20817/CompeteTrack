from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class MenuItemOut(BaseModel):
    id: UUID
    brand_id: UUID
    snapshot_id: UUID
    item_name: str
    category: Optional[str]
    price: Optional[Decimal]
    currency: str
    description: Optional[str]
    is_available: bool
    detected_at: date

    model_config = {"from_attributes": True}


class MenuSnapshotOut(BaseModel):
    id: UUID
    brand_id: UUID
    snapshot_date: date
    source: str
    item_count: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
