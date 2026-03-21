# CompeteTrack

## What This Project Is
越南餐飲業競品監控平台。自動追蹤競品的菜單、定價、營業時段變化，
偵測到變化時透過 Email 通知業者。
MVP 為自用（2 個自有品牌 + 3-5 個競品），架構預留 SaaS 多租戶擴充空間。

## Tech Stack
- Backend: Python FastAPI + APScheduler
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Database: Supabase (PostgreSQL)
- AI: Claude Sonnet API (繁體中文摘要)
- Email: SendGrid API
- Deployment: Zeabur (backend + frontend 各自獨立服務)

## Architecture Overview
- See docs/specs/api-spec.md for full API specification
- See docs/specs/data-model.md for complete database schema
- See docs/specs/integrations.md for external service configs
- See docs/architecture.md for system design decisions

## Critical Rules
1. ALL API responses MUST use: { success, data, error, timestamp }
2. NEVER hardcode credentials — always use environment variables via config.py
3. ALL database queries use SQLAlchemy ORM — never raw string SQL
4. user_id MUST be included in every table — MVP uses a fixed owner user
5. Snapshots are IMMUTABLE — never update a snapshot, always create new
6. Change Detector MUST be idempotent — running twice should not duplicate changes
7. All AI summaries MUST be in Traditional Chinese (繁體中文)
8. severity levels: high (>10% price change or new/removed item) | medium (5-10% change) | low (<5% change)
9. NEVER modify database schema directly — use Alembic migrations
10. Frontend MUST proxy all API calls through Next.js API routes (no direct FastAPI calls)

## Project Structure
```
competetrack/
├── backend/app/
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Pydantic Settings (env vars)
│   ├── database.py      # SQLAlchemy + Supabase connection
│   ├── scheduler.py     # APScheduler jobs
│   ├── api/             # Route handlers
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── workers/         # Data collectors (Google Places, Foody)
│   └── services/        # Business logic (change_detector, ai_analyzer)
└── frontend/app/        # Next.js app router
```

## Key Commands
- Backend dev: `cd backend && uvicorn app.main:app --reload --port 8000`
- Frontend dev: `cd frontend && npm run dev`
- Tests: `cd backend && pytest tests/ -v`
- DB migration: `cd backend && alembic upgrade head`
- Lint backend: `cd backend && ruff check .`
- Lint frontend: `cd frontend && npm run lint`

## Current Phase
Phase 1: 基礎建設
See docs/current-phase.md for detailed tasks and checklist.
