---
globs: ["backend/app/api/**", "backend/app/main.py"]
---

# API Conventions

## Response Format (MANDATORY for ALL endpoints)
```python
from app.schemas.response import APIResponse

return APIResponse(success=True, data=result)
# Never return raw dicts — always use APIResponse wrapper
```

## Error Handling
- Use HTTPException with proper status codes
- 404: resource not found
- 422: validation error (Pydantic handles automatically)
- 500: unexpected server error (log it, return generic message)

## Pagination
- All list endpoints support: ?limit=50&offset=0
- Default limit: 50, max: 200

## Route naming
- Use kebab-case for URL paths: /api/menu-items (not /api/menuItems)
- Plural nouns for collections: /api/brands (not /api/brand)
