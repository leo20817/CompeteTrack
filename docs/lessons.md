# Lessons Learned

## General
- Always build ALL database tables in Phase 1, even if the feature comes later.
  Past mistake: deferred social_snapshots, then had to alter schema after UI was done.
- Include user_id in every table from Day 1 for future multi-tenancy.
- Never use NEXT_PUBLIC_ prefix for API keys — only NEXT_PUBLIC_API_URL is allowed.

## Phase 1 Lessons
- Supabase pooler hostnames include a region code (e.g. `aws-1-ap-northeast-2`) — always copy from Dashboard, never guess.
- SQLAlchemy `server_default` must use `text("gen_random_uuid()")`, not bare strings — asyncpg treats strings as literal values.
- Passwords with special chars (like `*`) need URL-encoding (`%2A`) in DATABASE_URL.
- Alembic configparser interprets `%` — use `.replace("%", "%%")` when setting sqlalchemy.url programmatically.
- Keep `NEXT_PUBLIC_` vars out of backend .env, or set `extra="ignore"` in Pydantic Settings.
