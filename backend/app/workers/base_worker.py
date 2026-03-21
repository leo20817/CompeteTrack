import logging
from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Base class for all data collection workers."""

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    @abstractmethod
    async def collect(self, brand_id: UUID, place_id: str, snapshot_date: date) -> dict:
        """Collect data for a brand. Returns a summary dict."""
        ...
