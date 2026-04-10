# Implementation Plan: Portfolio Delivery & Economic Flow Governance Engine

**Branch**: `001-portfolio-delivery-engine` | **Date**: 2026-04-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-portfolio-delivery-engine/spec.md`

## Summary

A Python 3.12 analytics engine that computes four delivery health metrics
(Flow Efficiency, Cost of Delay, Cycle Time Distribution, ROI Scatter) across a
multi-workstream portfolio. Data is ingested from JSON + CSV files; output is an
interactive self-contained HTML dashboard (Plotly Dash) and CSV exports. OOP
architecture uses a Facade + Calculator pattern for clean separation and
independent testability of each metric domain.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: polars (data aggregation), plotly + dash (visualization),
pydantic v2 (input validation), pytest + pytest-benchmark (testing)
**Storage**: File-based (portfolio.json + work_item_events.csv); no database in v1
**Testing**: pytest + pytest-benchmark
**Target Platform**: Any OS with Python 3.12 (local execution, no server required)
**Project Type**: Analytics library + CLI entry point
**Performance Goals**: Full `calculate_all()` on 10k work items / 50 teams / 10 workstreams
in < 5 seconds; dashboard file generation in < 10 seconds
**Constraints**: Self-contained HTML output (no CDN, no server); no live integrations in v1
**Scale/Scope**: 10k work items, 50 teams, 10 workstreams

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First Development | ✅ PASS | Spec completed and quality-validated before this plan |
| II. User-Story-Centric Design | ✅ PASS | 4 independent user stories; each independently testable |
| III. Constitution-Gated Planning | ✅ PASS | This table IS the gate; re-evaluated below post-design |
| IV. Phase-Validated Execution | ✅ PASS | Task phases defined; each gated before the next |
| V. Simplicity & Minimalism | ✅ PASS | No database, no live integrations, file-based I/O |

**Complexity Tracking** (justified deviations):

| Deviation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Plotly Dash (adds server-like runtime during build) | US4 hover interactivity is a spec requirement (acceptance scenario 3) | Static matplotlib cannot satisfy FR-006 hover requirement |
| Polars over pure Python | SC-003 requires < 5s at 10k items; pure Python too slow | Benchmark data confirms Polars 10-50x faster for groupby aggregations |

**Post-design re-evaluation**: ✅ All principles still pass after Phase 1 design.
No new violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-portfolio-delivery-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── python-api.md    # DeliveryAnalyticsEngine class interface
│   ├── input-schema.md  # portfolio.json + work_item_events.csv schema
│   └── output-schema.md # CSV + HTML output format
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/
└── delivery_engine/
    ├── __init__.py
    ├── engine.py                   # DeliveryAnalyticsEngine (Facade)
    ├── models/
    │   ├── __init__.py
    │   ├── work_item.py            # WorkItem, StateTransition (dataclasses)
    │   ├── team.py                 # Team (dataclass)
    │   ├── workstream.py           # Workstream (dataclass)
    │   └── portfolio.py            # Portfolio (dataclass)
    ├── calculators/
    │   ├── __init__.py
    │   ├── flow_efficiency.py      # FlowEfficiencyCalculator (US1)
    │   ├── cost_of_delay.py        # CostOfDelayCalculator (US2)
    │   ├── cycle_time.py           # CycleTimeAnalyzer (US3)
    │   └── roi_scatter.py          # ROIScatterAnalyzer (US4)
    ├── io/
    │   ├── __init__.py
    │   ├── loader.py               # DataLoader (JSON + CSV → domain models)
    │   └── exporter.py             # ReportExporter (metrics → CSV + HTML)
    ├── dashboard/
    │   ├── __init__.py
    │   └── app.py                  # Plotly Dash layout + chart builders
    └── config.py                   # Default thresholds, state type mappings

tests/
├── __init__.py
├── fixtures/
│   ├── portfolio_minimal.json      # 2 workstreams, 3 teams
│   ├── portfolio_large.json        # 10 workstreams, 50 teams (perf tests)
│   ├── work_item_events_minimal.csv
│   └── work_item_events_large.csv  # 10k work items (perf tests)
├── unit/
│   ├── test_flow_efficiency.py     # US1 unit tests
│   ├── test_cost_of_delay.py       # US2 unit tests
│   ├── test_cycle_time.py          # US3 unit tests
│   ├── test_roi_scatter.py         # US4 unit tests
│   ├── test_loader.py              # DataLoader edge cases
│   └── test_exporter.py           # ReportExporter output validation
└── integration/
    ├── test_engine_minimal.py      # calculate_all() on minimal fixture
    └── test_engine_performance.py  # pytest-benchmark at 10k scale
```

**Structure Decision**: Single Python project at repo root. Analytics library pattern
(`src/` layout) enables both `import delivery_engine` usage and future CLI packaging.

---

## Phase 0: Research (Complete)

See [research.md](./research.md) for full findings.

**Key decisions**:
- Python 3.12, Polars, Plotly + Dash, Pydantic v2, pytest + pytest-benchmark
- Input: `portfolio.json` (hierarchy) + `work_item_events.csv` (one row per state transition)
- Output: self-contained HTML dashboard + 4 CSV files
- Architecture: Facade (`DeliveryAnalyticsEngine`) + 4 Calculator classes

All NEEDS CLARIFICATION resolved:
- State type mapping defaults defined in `config.py` (configurable)
- Currency configurable via `portfolio.json` → defaults USD
- Cycle time spread: IQR (P75 − P25); `high_variance = True` when IQR > 2 × median

---

## Phase 1: Design (Complete)

### Data Model

See [data-model.md](./data-model.md) for full entity definitions.

**Core entities**: Portfolio → Workstream → Team → WorkItem → StateTransition
**Computed**: DeliveryMetrics (produced by calculators, not stored)

**Critical computed fields on WorkItem**:
```
wait_time_days    = Σ duration(transitions where state_type == "wait")
active_time_days  = Σ duration(transitions where state_type == "active")
lead_time_days    = completed_at − first_transition.entered_at
cycle_time_days   = completed_at − first_active_transition.entered_at
cost_of_delay     = wait_time_days × team.resource_daily_rate
```

### Interface Contracts

See [contracts/](./contracts/):
- `python-api.md` — `DeliveryAnalyticsEngine`, `DataLoader`, `ReportExporter` class contracts
- `input-schema.md` — JSON + CSV input format with validation rules
- `output-schema.md` — CSV columns + HTML dashboard structure and interactivity requirements

### Metric Formulas

| Metric | Formula |
|--------|---------|
| Flow Efficiency | `(Σ active_time_days / Σ lead_time_days) × 100` per workstream |
| Cost of Delay | `wait_time_days × resource_daily_rate` per WorkItem; summed per team |
| Cycle Time Median | `median(cycle_time_days)` for completed WorkItems per priority tier |
| Cycle Time IQR | `P75(cycle_time_days) − P25(cycle_time_days)` per priority tier |
| High Variance | `IQR > 2 × median` → `True` |
| ROI Scatter | Plot: x = `lead_time_days`, y = `business_value` per WorkItem |

### Quickstart

See [quickstart.md](./quickstart.md) for integration test scenarios and edge case
validation examples.
