from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
