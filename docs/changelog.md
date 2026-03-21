# CompeteTrack Changelog

## Phase 1 — 基礎建設 (2026-03-21)
*Status: Complete*

### What was built
- **Project structure**: CLAUDE.md, .claude/rules/ (4 files), .env.example, .gitignore
- **Documentation**: architecture.md, current-phase.md, changelog.md, lessons.md, 3 spec files
- **Backend (FastAPI)**:
  - Config via Pydantic Settings (.env loading)
  - SQLAlchemy async engine + Supabase connection
  - All 8 SQLAlchemy models (users, brands, menu_snapshots, menu_items, brand_changes, hours_snapshots, notifications, social_snapshots)
  - Alembic migration (async) — all tables created in Supabase
  - GET /health endpoint (DB + env check)
  - Full brands CRUD (POST/GET/PUT/DELETE /api/brands)
  - APIResponse schema for unified { success, data, error, timestamp } format
- **Frontend (Next.js 14)**:
  - App router + Tailwind CSS
  - Layout with nav bar
  - Dashboard page with placeholder stats
  - API client lib (lib/api.ts)
  - Dockerfile (standalone output)

### Verification results
- [x] GET /health → {"success": true, "data": {"db": "connected", "env": "development"}}
- [x] POST /api/brands creates a brand successfully
- [x] GET /api/brands returns the created brand
- [x] Supabase Dashboard shows all 8 tables
- [x] Frontend builds without errors (`next build` passes)
- [ ] Zeabur deployment (pending user setup)

### Issues encountered & fixed
- Supabase pooler region was `ap-northeast-2`, not `ap-southeast-1` — caused "Tenant not found"
- `server_default="gen_random_uuid()"` treated as string literal by asyncpg — fixed with `text()`
- `NEXT_PUBLIC_API_URL` in backend .env caused pydantic validation error — added `extra="ignore"`
- `%` in password broke Alembic configparser — fixed with `.replace("%", "%%")`
