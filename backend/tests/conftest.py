import json
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import settings
from app.models.brand import User, Brand
from app.database import get_db
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest_asyncio.fixture
async def db_session():
    """Provide a test database session that rolls back after each test.

    Engine is created per-test to avoid asyncpg event loop mismatch.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        yield session
    finally:
        await trans.rollback()
        await session.close()
        await conn.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Provide a test HTTP client with DB override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def owner_user(db_session: AsyncSession) -> User:
    user = User(email=f"test-{uuid4().hex[:8]}@competetrack.com")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def sample_brand(db_session: AsyncSession, owner_user: User) -> Brand:
    brand = Brand(
        user_id=owner_user.id,
        name="Phở 24",
        brand_type="competitor",
        google_place_id="ChIJtest123",
    )
    db_session.add(brand)
    await db_session.flush()
    return brand


@pytest_asyncio.fixture
async def brand_no_place_id(db_session: AsyncSession, owner_user: User) -> Brand:
    brand = Brand(
        user_id=owner_user.id,
        name="No Place Brand",
        brand_type="own",
    )
    db_session.add(brand)
    await db_session.flush()
    return brand


@pytest.fixture
def places_response() -> dict:
    with open(FIXTURES_DIR / "google_places_response.json") as f:
        return json.load(f)


@pytest.fixture
def places_empty_response() -> dict:
    return {
        "html_attributions": [],
        "result": {
            "name": "Test Restaurant",
            "formatted_address": "123 Test St",
            "rating": 3.5,
            "user_ratings_total": 100,
        },
        "status": "OK",
    }


@pytest.fixture
def places_not_found_response() -> dict:
    return {"html_attributions": [], "result": {}, "status": "NOT_FOUND"}


@pytest.fixture
def places_denied_response() -> dict:
    return {
        "html_attributions": [],
        "status": "REQUEST_DENIED",
        "error_message": "API key invalid",
    }
