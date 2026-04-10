# Research: Portfolio Delivery & Economic Flow Governance Engine

**Branch**: `001-portfolio-delivery-engine` | **Date**: 2026-04-09
**Status**: Complete — all NEEDS CLARIFICATION resolved

## Decision 1: Python Version

**Decision**: Python 3.12
**Rationale**: 5-10% performance gains over 3.11 matter at 10k-item scale; improved error
messages accelerate debugging of metric calculation edge cases; LTS support through 2028.
**Alternatives considered**: Python 3.11 — production-stable but slower; Python 3.13 — too
new, ecosystem not fully settled.

## Decision 2: Data Processing Library

**Decision**: Polars
**Rationale**: 10-50x faster than pandas for the groupby-heavy aggregations needed for CoD
summation and flow efficiency across 10k items / 50 teams. LazyFrames enable streaming
evaluation. Built-in CSV reader eliminates a dependency. At the target scale (10k items,
50 teams) Polars keeps all operations under 1 second in benchmark.
**Alternatives considered**: pandas — higher memory overhead at scale, slower groupby;
pure Python — too slow for real-time filter/sort required by US3 and US4 views.

## Decision 3: Visualization Library

**Decision**: Plotly (plotly.express + plotly.graph_objects) with Plotly Dash for the
dashboard shell.
**Rationale**: Native hover interactivity satisfies the US4 acceptance scenario ("hover over
a data point → show name, value, lead time") without additional frontend code. Box plots
(US3), bar charts (US2), and scatter charts (US4) are all first-class Plotly primitives.
Dash provides a single-stack, file-servable dashboard without needing a separate frontend
framework. Output is a standalone HTML file.
**Alternatives considered**: Matplotlib/Seaborn — static only, fails US4 hover requirement;
Dash alone without Plotly.express — more boilerplate; Streamlit — requires running server,
heavier dependency footprint.

## Decision 4: Data Validation & Modeling

**Decision**: Pydantic v2 for input validation; Python dataclasses for internal domain
models.
**Rationale**: Pydantic v2 handles JSON deserialization and schema validation of WorkItem
state histories at the boundary (DataLoader). It produces clear, structured error messages
for malformed input (missing daily rates, invalid timestamps). Internal domain objects
(WorkItem, Team, Workstream, Portfolio) use plain dataclasses — lightweight, OOP-friendly,
no serialization overhead inside the engine.
**Alternatives considered**: dataclasses-only — no input validation; attrs — overkill for
this domain; Pydantic v1 — slower (v2 is ~20% faster); marshmallow — additional dep with
no benefit over Pydantic v2.

## Decision 5: Input Format

**Decision**: JSON for hierarchical structure (Portfolio → Workstreams → Teams);
CSV for bulk WorkItems (rows with state history encoded as JSON column or separate event
file).
**Rationale**: JSON captures the nested structure of the portfolio naturally. CSV scales
to 10k rows with fast Polars parsing. Avoids SQLite overhead for a stateless, file-based
v1. Both formats are exportable from any project management tool (Jira CSV export, Linear
JSON export).
**Input file layout**:
- `portfolio.json` — Portfolio, Workstreams, Teams, resource_daily_rates
- `work_items.csv` — one row per work item with computed wait/active time columns, OR
- `work_item_events.csv` — one row per state transition event (richer, enables engine
  to compute times itself)

**Alternatives considered**: SQLite — incompatible with stateless file-based assumption;
YAML — slower to parse, non-standard for tabular data; Excel — requires openpyxl, not
universally available.

## Decision 6: Output / Export Format

**Decision**: Interactive HTML (via Plotly Dash) for the dashboard; CSV for structured
data export (FR-009).
**Rationale**: HTML dashboards are file-shareable, require no server to view, and satisfy
SC-001 ("identify highest-CoD workstream within 2 minutes"). CSV enables stakeholders to
pivot in Excel/Sheets without additional tooling. Both formats require zero runtime
infrastructure for v1.
**Alternatives considered**: PDF — loses interactivity; Excel — requires openpyxl
dependency for a single export use case; PNG/SVG — static, breaks US4 hover requirement.

## Decision 7: Testing Framework

**Decision**: pytest with pytest-benchmark for performance validation.
**Rationale**: Fixture-based setup cleanly represents the Portfolio→Workstream→Team→
WorkItem hierarchy needed in unit tests. Parametrized tests validate metric accuracy (SC-002:
within 1% of manual calculation) across multiple datasets. pytest-benchmark validates SC-003
(responsiveness at 10k items / 50 teams / 10 workstreams).
**Alternatives considered**: unittest — more verbose, no built-in parametrize; nose —
deprecated; pytest alone without benchmark — cannot validate performance success criteria.

## Decision 8: OOP Architecture Pattern

**Decision**: Facade + Calculator pattern.
- `DeliveryAnalyticsEngine` is the Facade — single entry point for all metric computation.
- Each metric domain is a standalone Calculator class:
  - `FlowEfficiencyCalculator` (US1)
  - `CostOfDelayCalculator` (US2)
  - `CycleTimeAnalyzer` (US3)
  - `ROIScatterAnalyzer` (US4)
- `DataLoader` handles all I/O ingestion (JSON + CSV → domain models).
- `ReportExporter` handles all output (metrics → CSV + HTML).
- `DashApp` wraps the engine and renders Plotly charts.

**Rationale**: Facade hides internal complexity from callers; clients call
`engine.calculate_all()` or individual methods. Each Calculator is independently testable
without the engine. Decouples computation from rendering (Dash views never touch raw
Polars DataFrames directly). Enables future addition of new metric types without
touching existing calculators.
**Alternatives considered**: Pure Strategy pattern — lacks cohesion without a Facade
coordinator; Repository pattern — overkill with no persistence layer; Monolithic engine
class — violates single-responsibility, makes unit testing difficult.

## Resolved Clarifications

| # | Question | Resolution |
|---|----------|------------|
| 1 | Python version | 3.12 (performance + LTS) |
| 2 | Input format for state history | `work_item_events.csv` (one row per transition) + `portfolio.json` |
| 3 | Dashboard delivery mechanism | Standalone HTML file via Plotly Dash (no server required for v1) |
| 4 | Currency for CoD output | Configurable via `portfolio.json`; defaults to USD |
| 5 | Cycle time variance metric | Display IQR (interquartile range) alongside median as spread measure |
