# CompeteTrack Architecture

## System Overview
CompeteTrack is a competitive intelligence platform for Vietnam F&B businesses.
It automatically monitors competitor menus, pricing, and business hours,
then notifies operators via email when changes are detected.

## Component Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Next.js 14  │────▶│  FastAPI Backend │────▶│   Supabase   │
│  (Frontend)  │◀────│   (Port 8000)   │◀────│ (PostgreSQL) │
│  Port 3000   │     └────────┬────────┘     └──────────────┘
└─────────────┘              │
                    ┌────────┴────────┐
                    │   Workers &      │
                    │   Services       │
                    ├──────────────────┤
                    │ Google Places    │──▶ Google Maps API
                    │ Foody Scraper    │──▶ Foody.vn
                    │ Change Detector  │
                    │ AI Analyzer      │──▶ Claude Sonnet API
                    │ Email Notifier   │──▶ SendGrid API
                    │ APScheduler      │
                    └──────────────────┘
```

## Key Design Decisions

### 1. Snapshot + Diff Architecture
Every crawl stores a complete snapshot. Change Detector compares latest vs previous.
This ensures full history and easy debugging — we can replay any point in time.

### 2. social_snapshots from Day 1
Table created in Phase 1 even though crawlers come in Phase 2+.
Avoids schema changes after UI is built.

### 3. user_id on all tables
MVP uses a single fixed user. When SaaS launches, multi-tenancy works without schema changes.

### 4. Frontend API Proxy
All frontend API calls go through Next.js API routes → FastAPI.
Avoids CORS issues and hides backend URL from clients.

## Data Flow (Daily at 08:00 VN time)
1. APScheduler triggers crawl for all active brands
2. Workers fetch data from Google Places / Foody.vn
3. Data stored as immutable snapshots
4. Change Detector compares latest vs previous snapshot
5. Claude Sonnet generates Traditional Chinese summaries for changes
6. Email notifications sent (immediate for high severity, daily digest for others)
