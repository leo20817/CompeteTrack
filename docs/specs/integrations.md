# External Service Integrations

## Google Places API
- SDK: googlemaps Python SDK (`pip install googlemaps`)
- Key: `GOOGLE_PLACES_API_KEY` (server-side only, never NEXT_PUBLIC_)
- Endpoints used:
  - `place_details(place_id, fields=['name','opening_hours','popular_times','rating','user_ratings_total','price_level','menu'])`
- Rate limits: 100 QPS
- Cost: ~$17 per 1000 Place Details calls (budget: < $5/month for 5 brands)
- Error handling: If place_id invalid → log warning, skip, do NOT crash

## Claude Sonnet API (AI Summaries)
- Model: claude-sonnet-4-5 (latest Sonnet)
- Key: `CLAUDE_API_KEY` (server-side only)
- Usage: 1 API call per brand_change detected
- Max tokens: 100 (summaries are short)
- Timeout: 10 seconds per call
- Error handling: failure → ai_summary = NULL, log error, continue

## SendGrid (Email)
- Key: `SENDGRID_API_KEY` (server-side only)
- From: notifications@[your-domain] (must verify sender in SendGrid)
- Templates: HTML inline (no SendGrid dynamic templates for MVP)
- Error handling: failure → log error, update notifications.status='failed'

## Supabase
- Connection: `DATABASE_URL` (PostgreSQL connection string)
- Use SQLAlchemy async engine (not Supabase Python client)
- `SUPABASE_URL` and `SUPABASE_ANON_KEY`: reserved for future auth, not used in MVP
