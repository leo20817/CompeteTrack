# Current Phase: Phase 4 — Email 通知

## Goal
Send email digests when brand changes are detected, using SendGrid API.

## Tasks
- [ ] 4.1 Email service — SendGrid integration
- [ ] 4.2 Digest builder — aggregate unnotified changes into HTML email
- [ ] 4.3 APScheduler — daily scheduled crawl + change detection + email
- [ ] 4.4 Manual trigger API — POST /api/notifications/send-digest

## Previous Phases
- Phase 1: 基礎建設 — completed 2026-03-21
- Phase 2: Google Places 爬蟲 — completed 2026-03-21
- Phase 3: Change Detector — completed 2026-03-21
