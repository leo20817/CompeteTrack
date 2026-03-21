from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BrandChangeOut(BaseModel):
    id: UUID
    brand_id: UUID
    change_type: str
    severity: str
    field_changed: str
    old_value: Optional[dict]
    new_value: dict
    ai_summary: Optional[str]
    old_snapshot_id: Optional[UUID]
    new_snapshot_id: Optional[UUID]
    detected_at: datetime
    notified_at: Optional[datetime]

    model_config = {"from_attributes": True}
