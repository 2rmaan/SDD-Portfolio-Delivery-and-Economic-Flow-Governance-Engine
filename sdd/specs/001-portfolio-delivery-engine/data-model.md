# Data Model: Portfolio Delivery & Economic Flow Governance Engine

**Branch**: `001-portfolio-delivery-engine` | **Date**: 2026-04-09

## Entity Overview

```
Portfolio
└── Workstream (1..*)
    └── Team (1..*)
        └── WorkItem (0..*)
            └── StateTransition (1..*)

DeliveryMetrics (computed — one per entity level)
```

---

## Core Domain Models

### Portfolio

The top-level container aggregating all workstreams for cross-cutting metric views.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `id` | str | Yes | Non-empty, unique |
| `name` | str | Yes | Non-empty |
| `currency` | str | No | ISO 4217 code; defaults to "USD" |
| `workstream_ids` | list[str] | Yes | Must reference valid Workstream ids |

**Relationships**: Portfolio 1 → N Workstream

---

### Workstream

A logical grouping of teams (e.g., "Cloud Infrastructure", "Gamma Team").

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `id` | str | Yes | Non-empty, unique |
| `name` | str | Yes | Non-empty |
| `portfolio_id` | str | Yes | Must reference a valid Portfolio id |
| `flow_efficiency_threshold` | float | No | 0.0–1.0; defaults to 0.45 |
| `team_ids` | list[str] | Yes | Must reference valid Team ids; non-empty |

**Relationships**: Workstream N → 1 Portfolio; Workstream 1 → N Team

---

### Team

A delivery team with an associated resource cost.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `id` | str | Yes | Non-empty, unique |
| `name` | str | Yes | Non-empty |
| `workstream_id` | str | Yes | Must reference a valid Workstream id |
| `resource_daily_rate` | float | Yes | > 0.0; represents cost per calendar day in portfolio currency |

**Relationships**: Team N → 1 Workstream; Team 1 → N WorkItem

**Edge case**: If `resource_daily_rate` is missing, the Team is excluded from CoD calculation
and a warning is emitted. It still participates in flow efficiency and cycle time views.

---

### WorkItem

Represents a ticket, story, or feature being tracked through delivery states.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `id` | str | Yes | Non-empty, unique |
| `title` | str | Yes | Non-empty |
| `priority` | str | Yes | One of: P0, P1, P2, P3, Critical, High, Medium, Low |
| `business_value` | float | No | 0.0–100.0; required for ROI scatter (US4); null excluded from US4 |
| `team_id` | str | Yes | Must reference a valid Team id |
| `state_transitions` | list[StateTransition] | Yes | Non-empty; must contain at least one transition |

**Computed fields** (derived at load time from state_transitions):

| Computed Field | Formula |
|----------------|---------|
| `wait_time_days` | Sum of durations where `StateTransition.state_type == "wait"` |
| `active_time_days` | Sum of durations where `StateTransition.state_type == "active"` |
| `lead_time_days` | `completed_at` − `first_transition.entered_at` |
| `cycle_time_days` | `completed_at` − `first_active_transition.entered_at` |
| `is_completed` | True if any StateTransition has `state == "completed"` |
| `cost_of_delay` | `wait_time_days × team.resource_daily_rate` |

**Edge cases**:
- WorkItem with no wait-state transitions → `wait_time_days = 0`, `cost_of_delay = 0`
- WorkItem not yet completed → excluded from cycle time distribution; included in CoD if
  currently in a wait state (ongoing wait calculated to "now")
- WorkItem with `business_value = null` → excluded from ROI scatter only

---

### StateTransition

Records a single state change for a WorkItem.

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `work_item_id` | str | Yes | Must reference a valid WorkItem id |
| `state` | str | Yes | Non-empty; free-text label from the source tool |
| `state_type` | str | Yes | One of: "active", "wait", "completed"; mapped at load time |
| `entered_at` | datetime | Yes | ISO 8601 with timezone |
| `exited_at` | datetime | No | ISO 8601 with timezone; null if current state |

**State type mapping** (configurable; defaults):

| State label patterns | Mapped type |
|----------------------|-------------|
| "In Progress", "Active", "Development", "Review" | `active` |
| "Waiting", "Blocked", "In Queue", "Pending Approval", "Started" | `wait` |
| "Done", "Completed", "Closed", "Delivered" | `completed` |
| "Created", "Backlog", "To Do" | `wait` (pre-start wait) |

**Validation rules**:
- `exited_at` MUST be after `entered_at` when present
- Transitions for a WorkItem MUST be chronologically ordered
- A WorkItem MUST NOT have overlapping transitions

---

## Computed Output Model

### DeliveryMetrics

Produced by the engine calculators; not stored as input — computed on demand.

| Field | Type | Produced by |
|-------|------|-------------|
| `entity_id` | str | All calculators |
| `entity_type` | str ("workstream" / "team" / "work_item") | All |
| `flow_efficiency_pct` | Optional[float] | FlowEfficiencyCalculator |
| `below_threshold` | Optional[bool] | FlowEfficiencyCalculator |
| `total_cost_of_delay` | Optional[float] | CostOfDelayCalculator |
| `work_item_cod_breakdown` | Optional[list[dict]] | CostOfDelayCalculator |
| `cycle_time_median_days` | Optional[float] | CycleTimeAnalyzer |
| `cycle_time_iqr_days` | Optional[float] | CycleTimeAnalyzer |
| `lead_time_days` | Optional[float] | ROIScatterAnalyzer |
| `business_value` | Optional[float] | ROIScatterAnalyzer |

---

## Input File Schemas

### `portfolio.json`

```json
{
  "id": "portfolio-001",
  "name": "Enterprise Software Portfolio",
  "currency": "USD",
  "workstreams": [
    {
      "id": "ws-cloud",
      "name": "Cloud Infrastructure",
      "flow_efficiency_threshold": 0.45,
      "teams": [
        {
          "id": "team-alpha",
          "name": "Alpha Team",
          "resource_daily_rate": 2500.00
        }
      ]
    }
  ]
}
```

### `work_item_events.csv`

```
work_item_id,title,priority,business_value,team_id,state,state_type,entered_at,exited_at
WI-001,Deploy Auth Service,P0,90,team-alpha,Backlog,wait,2026-01-01T08:00:00Z,2026-01-03T09:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,In Progress,active,2026-01-03T09:00:00Z,2026-01-06T17:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,Waiting for Review,wait,2026-01-06T17:00:00Z,2026-01-08T10:00:00Z
WI-001,Deploy Auth Service,P0,90,team-alpha,Completed,completed,2026-01-08T10:00:00Z,
```

---

## State Machine

```
[Created/Backlog] → [In Progress] ⇄ [Waiting/Blocked] → [Completed]
     (wait)             (active)          (wait)           (terminal)
```

A WorkItem may cycle between `active` and `wait` states multiple times before
reaching `completed`. Each cycle is recorded as separate StateTransition rows.
