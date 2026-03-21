# Lessons Learned

## General
- Always build ALL database tables in Phase 1, even if the feature comes later.
  Past mistake: deferred social_snapshots, then had to alter schema after UI was done.
- Include user_id in every table from Day 1 for future multi-tenancy.
- Never use NEXT_PUBLIC_ prefix for API keys — only NEXT_PUBLIC_API_URL is allowed.

## Phase 3 Lessons
- Python 3.9 does not support `X | None` union syntax — always use `Optional[X]` from typing.
- Change detector idempotency must check item_name inside JSONB, not just (snapshot_id, change_type) — otherwise two different items with the same change_type would be treated as duplicates.

## Phase 2 Lessons
- SQLite cannot be used for tests when models use PostgreSQL-specific types (ARRAY, JSONB) — use real PostgreSQL with transaction rollback instead.
- asyncpg connections are bound to the event loop that created them — create a new engine per test function to avoid "attached to a different loop" errors.
- `httpx.Response(200, json=data)` requires a `request=` parameter for `.raise_for_status()` to work — always provide a mock `httpx.Request` object.
- Google Places API does not return structured menu data — `menu` field returns nothing useful. Menu data will need to come from Foody.vn or manual entry.
- Google Places API requires both "Places API" enabled AND billing linked to the project — enabling one without the other still returns REQUEST_DENIED.

## Phase 1 Lessons
- Supabase pooler hostnames include a region code (e.g. `aws-1-ap-northeast-2`) — always copy from Dashboard, never guess.
- SQLAlchemy `server_default` must use `text("gen_random_uuid()")`, not bare strings — asyncpg treats strings as literal values.
- Passwords with special chars (like `*`) need URL-encoding (`%2A`) in DATABASE_URL.
- Alembic configparser interprets `%` — use `.replace("%", "%%")` when setting sqlalchemy.url programmatically.
- Keep `NEXT_PUBLIC_` vars out of backend .env, or set `extra="ignore"` in Pydantic Settings.
