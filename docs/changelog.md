# CompeteTrack Changelog

## Phase 2 — Google Places 爬蟲 (2026-03-21)
*Status: In Progress (awaiting API key activation for live test)*

### What was built
- **Google Places Worker** (`backend/app/workers/google_places.py`):
  - Async httpx client with context manager
  - Fetches place details (name, hours, rating, price_level, menu)
  - Parses opening_hours periods into `{day: {open, close, is_closed}}` format
  - Handles weekday_text fallback when periods are empty
  - Graceful handling: no menu → empty list + warning, no hours → empty dict
  - popular_times → NULL (not available in official API)
- **Collect endpoint** (`POST /api/brands/{id}/collect`):
  - Validates brand exists + has google_place_id + API key configured
  - Creates immutable menu_snapshot with raw_data
  - Creates menu_items from parsed data
  - Creates hours_snapshot with hours_data and popular_times
  - Running collect twice creates 2 separate snapshots (immutability verified)
- **Menu endpoints**:
  - `GET /api/menu/{brand_id}` — returns latest snapshot + items
  - `GET /api/menu/{brand_id}/snapshots` — paginated snapshot list
- **Test suite** (20 tests, all passing):
  - `test_google_places_worker.py` — 8 tests (worker unit tests with mocked httpx)
  - `test_collect.py` — 6 tests (endpoint happy path + error cases)
  - `test_menu.py` — 6 tests (GET menu + snapshots)
  - Test infra: conftest.py with transaction rollback, static fixture data

### Verification results
- [x] All 20 tests pass (`pytest tests/ -v`)
- [x] Worker correctly parses hours from Google Places periods format
- [x] Snapshots are immutable (collect twice → 2 rows)
- [x] Missing data handled gracefully (no crash on empty hours/menu)
- [ ] Live test with real API key (pending billing activation)

### Issues encountered & fixed
- SQLite can't handle PostgreSQL ARRAY/JSONB types — switched tests to real Supabase with transaction rollback
- asyncpg connections bound to event loop — create engine per-test to avoid mismatch
- `httpx.Response.raise_for_status()` needs `request` param — added helper `_mock_response()`
- `menu` field was missing from PLACE_DETAILS_FIELDS — added per integrations.md spec

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
