# Contract: Input Data Schema

**Type**: File-based input format (JSON + CSV)
**Version**: v1

---

## File 1: `portfolio.json`

Defines the portfolio hierarchy: Portfolio → Workstreams → Teams.

### Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "name", "workstreams"],
  "properties": {
    "id":         { "type": "string", "minLength": 1 },
    "name":       { "type": "string", "minLength": 1 },
    "currency":   { "type": "string", "default": "USD", "pattern": "^[A-Z]{3}$" },
    "workstreams": {
      "type": "array", "minItems": 1,
      "items": {
        "required": ["id", "name", "teams"],
        "properties": {
          "id":   { "type": "string", "minLength": 1 },
          "name": { "type": "string", "minLength": 1 },
          "flow_efficiency_threshold": {
            "type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.45
          },
          "teams": {
            "type": "array", "minItems": 1,
            "items": {
              "required": ["id", "name", "resource_daily_rate"],
              "properties": {
                "id":                  { "type": "string", "minLength": 1 },
                "name":                { "type": "string", "minLength": 1 },
                "resource_daily_rate": { "type": "number", "exclusiveMinimum": 0 }
              }
            }
          }
        }
      }
    }
  }
}
```

### Example

```json
{
  "id": "portfolio-2026",
  "name": "Enterprise Software Portfolio",
  "currency": "USD",
  "workstreams": [
    {
      "id": "ws-cloud",
      "name": "Cloud Infrastructure",
      "flow_efficiency_threshold": 0.45,
      "teams": [
        { "id": "team-alpha", "name": "Alpha Team", "resource_daily_rate": 2500.00 },
        { "id": "team-beta",  "name": "Beta Team",  "resource_daily_rate": 3000.00 }
      ]
    },
    {
      "id": "ws-product",
      "name": "Product Engineering",
      "flow_efficiency_threshold": 0.50,
      "teams": [
        { "id": "team-gamma", "name": "Gamma Team", "resource_daily_rate": 2800.00 }
      ]
    }
  ]
}
```

---

## File 2: `work_item_events.csv`

One row per state transition event. The engine groups rows by `work_item_id` to
reconstruct full WorkItem histories.

### Column Definitions

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `work_item_id` | string | Yes | Unique work item identifier |
| `title` | string | Yes | Human-readable name |
| `priority` | string | Yes | One of: P0, P1, P2, P3, Critical, High, Medium, Low |
| `business_value` | float \| empty | No | 0–100; leave blank if not scored |
| `team_id` | string | Yes | Must match a Team id in portfolio.json |
| `state` | string | Yes | State label as recorded in source tool |
| `state_type` | string | Yes | One of: `active`, `wait`, `completed` |
| `entered_at` | ISO 8601 datetime | Yes | When this state was entered (UTC recommended) |
| `exited_at` | ISO 8601 datetime \| empty | No | When state was exited; blank = current state |

### Validation Rules

- All `work_item_id` + `team_id` combinations must be consistent within the file
  (a work item cannot belong to two different teams)
- `exited_at` must be after `entered_at` when present
- Rows for the same `work_item_id` must be in chronological order
- `team_id` must reference a team defined in `portfolio.json`

### Example

```csv
work_item_id,title,priority,business_value,team_id,state,state_type,entered_at,exited_at
WI-001,Deploy Auth Service,P0,90,team-alpha,Backlog,wait,2026-01-01T08:00:00Z,2026-01-03T09:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,In Progress,active,2026-01-03T09:00:00Z,2026-01-06T17:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,Waiting for Review,wait,2026-01-06T17:00:00Z,2026-01-08T10:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,Completed,completed,2026-01-08T10:00:00Z,
WI-002,Migrate DB Schema,Medium,,team-gamma,Backlog,wait,2026-01-05T08:00:00Z,2026-01-10T09:00:00Z
WI-002,Migrate DB Schema,Medium,,team-gamma,In Progress,active,2026-01-10T09:00:00Z,2026-01-15T17:00:00Z
WI-002,Migrate DB Schema,Medium,,team-gamma,Blocked,wait,2026-01-15T17:00:00Z,2026-01-20T10:00:00Z
WI-002,Migrate DB Schema,Medium,,team-gamma,In Progress,active,2026-01-20T10:00:00Z,2026-01-22T16:00:00Z
WI-002,Migrate DB Schema,Medium,,team-gamma,Completed,completed,2026-01-22T16:00:00Z,
```

---

## Validation Behaviour

| Condition | Engine Behaviour |
|-----------|-----------------|
| Missing `resource_daily_rate` for a team | Team excluded from CoD; warning logged |
| `business_value` blank for a WorkItem | WorkItem excluded from ROI scatter only |
| `team_id` in CSV not in portfolio.json | `ReferenceError` raised; load aborted |
| Overlapping state transitions | `ValidationError` raised for that WorkItem |
| No completed WorkItems | `InsufficientDataError` for cycle time only |
| WorkItem in active wait state (no exited_at) | CoD calculated to current timestamp |
