---
globs: ["backend/tests/**"]
---

# Testing Rules
- Every API endpoint: at least 1 happy-path + 1 error test
- Use pytest fixtures for database setup/teardown
- Mock ALL external API calls (Google Places, Claude, SendGrid) → Never hit real services in tests
- Test file naming: test_{module_name}.py
- Change Detector tests: use static fixture data, not real snapshots
