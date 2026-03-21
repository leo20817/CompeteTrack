---
globs: ["Dockerfile", "docker-compose*.yml", ".env*", "zeabur.json"]
---

# Deployment Rules
- NEVER commit .env files — .env.example only
- All secrets via Zeabur environment variables
- Health check: GET /health MUST always exist and return 200
- Backend port: 8000, Frontend port: 3000
- Backend and Frontend are SEPARATE Zeabur services
- Frontend communicates to Backend via NEXT_PUBLIC_API_URL env var
  → This is the only NEXT_PUBLIC_ variable — all others are server-side only
