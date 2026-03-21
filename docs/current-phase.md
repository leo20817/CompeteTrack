# Current Phase: Phase 2 — Google Places 爬蟲

## Goal
Crawl real brand data (menus, hours, ratings) from Google Places API and store as snapshots.

## Tasks
- [ ] 2.1 Google Places Worker — fetch place details (menu, hours, popular_times, rating)
- [ ] 2.2 Data parser — parse Places API response into menu_items structure
- [ ] 2.3 Manual trigger API — POST /api/brands/{id}/collect
- [ ] 2.4 Error handling — missing menu fallback, rate limiting, retries

## Verification Checklist
- [ ] Add brand with valid google_place_id
- [ ] POST /api/brands/{id}/collect → 200 OK
- [ ] menu_snapshots has new row with raw_data
- [ ] menu_items has structured items (at least 3 rows)
- [ ] hours_snapshots has opening hours data
- [ ] Second collect creates a second snapshot (no upsert)

## Previous Phase
Phase 1: 基礎建設 — completed 2026-03-21
