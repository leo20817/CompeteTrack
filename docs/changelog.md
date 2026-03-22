# CompeteTrack Changelog

## Phase 6 — 社群媒體監控 (2026-03-22)
*Status: Complete (awaiting Apify API token for live test)*

### What was built
- **Apify Workers** (3 platform collectors):
  - `apify_tiktok.py`: TikTok profile + videos via `clockworks/free-tiktok-scraper`
  - `apify_instagram.py`: Instagram profile + posts via `apify/instagram-profile-scraper`
  - `apify_facebook.py`: Facebook page info via `apify/facebook-pages-scraper`
  - All async (httpx), 120s timeout, graceful failure handling
- **Database**: Alembic migration adds `tiktok_username`, `instagram_username`, `facebook_url` to brands
- **Social API** (`GET /api/social/{brand_id}`): returns latest snapshot for all 3 platforms
- **Social Change Detector**: detects follower changes (>5% = high), viral content (>100K views), engagement rate changes
- **Scheduler**: social collection at 09:00 VN time daily
- **Collect endpoint**: now also triggers social collection when Apify configured
- **Frontend**: 社群媒體 sidebar tab with 3 platform cards + top posts grid
  - Empty states: "尚未設定帳號" / "尚未收集資料"
- **Tests** (6 new, all passing): TikTok/Instagram/Facebook happy path + empty responses

### Metrics JSONB structure
- TikTok: total_likes, video_count, avg_views, avg_likes, avg_comments, avg_shares, engagement_rate
- Instagram: avg_likes, avg_comments, engagement_rate, reels_count, avg_reel_views
- Facebook: page_likes, rating, review_count, checkins, talking_about

## Phase 4 — Email 通知系統 (2026-03-22)
*Status: Complete*

### What was built
- **Email Notifier** (`backend/app/services/email_notifier.py`):
  - SendGrid HTTP API integration (async httpx)
  - Immediate alert for high severity changes
  - Daily digest grouped by brand (high + medium)
  - "No changes" digest sends "今日無競品異動，市場穩定。"
  - HTML email templates with severity badges and CTA buttons
  - All sends wrapped in try/except — failure → status='failed', no crash
- **Scheduler** (`backend/app/scheduler.py`):
  - APScheduler with Asia/Ho_Chi_Minh timezone
  - 08:00 daily: collect all brands + detect changes
  - 08:30 daily: send digest email
  - Started/stopped via FastAPI lifespan
- **Scheduler API** (`backend/app/api/scheduler_api.py`):
  - `GET /api/scheduler/status` — scheduler status + next run times
  - `POST /api/scheduler/run-daily-digest` — manual trigger
- **Change Detector Integration**:
  - Immediate alert triggered after detecting high severity changes
  - Passes SendGrid config from settings
- **Test suite** (8 new tests, 37 total, all passing):
  - Immediate alert: sends, skips non-high, skips already-notified
  - SendGrid failure creates notification with status='failed'
  - Daily digest: with changes, no changes, failure handling
  - Notification record creation verified

### Verification results
- [x] 37 total tests pass
- [x] Immediate alert only for severity='high'
- [x] SendGrid failure → status='failed', error_msg set, no crash
- [x] Daily digest includes brand grouping and severity badges
- [x] Duplicate prevention: skips changes with notified_at already set
- [ ] Live email test (pending SendGrid API key setup)

## Phase 3 — Change Detector (2026-03-21)
*Status: Complete*

### What was built
- **Change Detector** (`backend/app/services/change_detector.py`):
  - Compares two most recent menu_snapshots for a brand
  - Detects: price_increase, price_decrease, new_item, removed_item
  - Severity: high (>10% or new/removed), medium (5-10%), low (<5%)
  - Idempotent — running twice on same snapshot pair produces no duplicates
  - Deduplication by (brand_id, old_snapshot_id, new_snapshot_id, field_changed, change_type, item_name)
- **AI Analyzer** (`backend/app/services/ai_analyzer.py`):
  - Claude Sonnet API integration for Traditional Chinese summaries
  - Graceful failure — ai_summary=NULL on error, no crash
  - Max 100 tokens, 10s timeout per integrations.md spec
- **Changes API** (`backend/app/api/changes.py`):
  - `GET /api/changes` — list with brand_id/severity filters + pagination
  - `GET /api/changes/unnotified` — unnotified changes
  - `PATCH /api/changes/{id}/read` — mark as notified
  - `POST /api/changes/detect/{brand_id}` — manual trigger
- **Test suite** (9 tests, all passing):
  - Price increase high/medium/low severity detection
  - New item and removed item detection
  - Idempotency verification
  - AI failure graceful handling
  - No API key → NULL summary without crash

### Verification results
- [x] 29 total tests pass (9 change detector + 20 existing)
- [x] Price change >10% → severity=high
- [x] Price change 5-10% → severity=medium
- [x] Price change <5% → severity=low
- [x] New/removed items → severity=high
- [x] Idempotent — second run returns 0 new changes
- [x] AI failure → ai_summary=NULL, no crash

### Issues encountered & fixed
- Python 3.9 doesn't support `str | None` union syntax — use `Optional[str]` instead

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
