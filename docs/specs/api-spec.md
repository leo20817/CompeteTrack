# API Specification

## Response Format (ALL endpoints)
```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-03-21T08:00:00Z"
}
```

## Phase 1 Endpoints

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | DB connection + env check |

### Brands
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/brands | List all brands (?limit=50&offset=0) |
| POST | /api/brands | Create brand |
| GET | /api/brands/{id} | Get brand detail |
| PUT | /api/brands/{id} | Update brand |
| DELETE | /api/brands/{id} | Soft-delete (is_active=false) |

## Future Endpoints (Phase 2+)

### Brand Actions
| POST | /api/brands/{id}/collect | Trigger crawl |
| POST | /api/brands/{id}/aliases | Add custom alias |

### Changes
| GET | /api/changes | All changes (filter: brand_id, severity, date range) |
| GET | /api/changes/{brand_id} | Brand's change history |
| GET | /api/changes/unnotified | Unnotified changes |
| PATCH | /api/changes/{id}/read | Mark as read |

### Menu
| GET | /api/menu/{brand_id} | Latest menu |
| GET | /api/menu/{brand_id}/snapshots | Snapshot list |
| GET | /api/menu/{brand_id}/diff | Diff between snapshots |
| GET | /api/menu/{brand_id}/history/{item_name} | Item price history |

### Dashboard
| GET | /api/dashboard/summary | Overview stats |
| GET | /api/dashboard/timeline | Change timeline (30 days) |
| GET | /api/dashboard/price-comparison | Multi-brand price comparison |
| GET | /api/dashboard/hours-comparison | Multi-brand hours comparison |

### Scheduler
| GET | /api/scheduler/status | Scheduler status |
| POST | /api/scheduler/run-now | Manual full crawl |
| GET | /api/notifications/history | Notification history |
