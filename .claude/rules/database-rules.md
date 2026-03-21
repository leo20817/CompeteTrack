---
globs: ["backend/app/models/**", "backend/app/database.py", "backend/alembic/**"]
---

# Database Rules

## Schema Rules
- ALL tables: id (UUID, default gen_random_uuid()), created_at, updated_at
- ALL tables: user_id UUID FK → users(id)
- Foreign keys MUST specify ON DELETE behavior (CASCADE or SET NULL)
- Index ALL foreign key columns
- JSONB columns for flexible data (snapshots, metrics)

## Migration Rules
- NEVER modify Supabase tables directly in production
- ALL schema changes via Alembic: `alembic revision --autogenerate -m 'description'`
- Test migration: `alembic upgrade head && alembic downgrade -1`

## Query Rules
- Use SQLAlchemy ORM — no raw SQL strings
- Always use async sessions: `async with AsyncSession(engine) as session`
- Snapshots are IMMUTABLE — never UPDATE a snapshot row
