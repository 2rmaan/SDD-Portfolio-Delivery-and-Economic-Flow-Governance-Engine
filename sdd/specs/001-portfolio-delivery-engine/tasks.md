---
description: "Task list for Portfolio Delivery & Economic Flow Governance Engine"
---

# Tasks: Portfolio Delivery & Economic Flow Governance Engine

**Input**: Design documents from `specs/001-portfolio-delivery-engine/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks generated. Test fixtures are included
where they enable independent validation of each user story per quickstart.md scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths are included in every task description

## Path Conventions

- **Source**: `src/delivery_engine/` at repository root
- **Tests**: `tests/` at repository root
- **Single project** layout (per plan.md)

---

## Phase 1: Setup

**Purpose**: Project initialization and package structure

- [X] T001 Create `pyproject.toml` at repo root with Python 3.12 requirement and dependencies: polars, plotly, dash, pydantic>=2.0, pytest, pytest-benchmark; add `[project.scripts]` entry `delivery-engine = "delivery_engine.cli:main"` (placeholder)
- [X] T002 [P] Create `src/delivery_engine/` package directory tree: `models/`, `calculators/`, `io/`, `dashboard/` — add empty `__init__.py` to each
- [X] T003 [P] Create `tests/` directory tree: `unit/`, `integration/`, `fixtures/` — add empty `__init__.py` to `tests/`, `tests/unit/`, `tests/integration/`
- [X] T004 [P] Create `.gitignore` at repo root with Python patterns: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`, `.pytest_cache/`, `.DS_Store`, `output/`

**Checkpoint**: Project skeleton in place — all directories and config exist before any source code is written.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain models and data loading infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [P] Create `src/delivery_engine/config.py` with: `DEFAULT_FLOW_EFFICIENCY_THRESHOLD = 0.45`, `STATE_TYPE_MAP` dict mapping state label patterns to `"active"`, `"wait"`, or `"completed"` (use patterns from data-model.md), and `HIGH_VARIANCE_MULTIPLIER = 2.0`
- [X] T006 [P] Implement `WorkItem` and `StateTransition` dataclasses in `src/delivery_engine/models/work_item.py`: StateTransition fields (`work_item_id`, `state`, `state_type`, `entered_at`, `exited_at`); WorkItem fields (`id`, `title`, `priority`, `business_value`, `team_id`, `state_transitions`); add `@property` computed fields: `wait_time_days`, `active_time_days`, `lead_time_days`, `cycle_time_days`, `is_completed`, `cost_of_delay` (requires `team_daily_rate` param)
- [X] T007 [P] Implement `Team` dataclass in `src/delivery_engine/models/team.py`: fields `id`, `name`, `workstream_id`, `resource_daily_rate: float | None`
- [X] T008 [P] Implement `Workstream` dataclass in `src/delivery_engine/models/workstream.py`: fields `id`, `name`, `portfolio_id`, `flow_efficiency_threshold: float = 0.45`, `team_ids: list[str]`
- [X] T009 [P] Implement `Portfolio` dataclass in `src/delivery_engine/models/portfolio.py`: fields `id`, `name`, `currency: str = "USD"`, `workstreams: list[Workstream]`; add helper `get_team(team_id) -> Team | None` and `get_workstream(workstream_id) -> Workstream | None`
- [X] T010 [P] Update `src/delivery_engine/models/__init__.py` to export `WorkItem`, `StateTransition`, `Team`, `Workstream`, `Portfolio` from their respective modules
- [X] T011 Implement `DataLoader` class in `src/delivery_engine/io/loader.py` with two static methods: (1) `load_portfolio(path: str) -> Portfolio` — reads `portfolio.json`, validates with Pydantic v2 schema matching `contracts/input-schema.md`, raises `ValidationError` on schema violations; (2) `load_work_items(path: str, portfolio: Portfolio) -> list[WorkItem]` — reads `work_item_events.csv` with Polars, groups rows by `work_item_id` to build `StateTransition` lists, raises `ReferenceError` if `team_id` not in portfolio, raises `ValidationError` on chronology violations (depends on T006–T010)
- [X] T012 Create `DeliveryAnalyticsEngine` skeleton class in `src/delivery_engine/engine.py`: `__init__(self, portfolio: Portfolio)` stores portfolio and validates at least one workstream exists (raises `ValueError` otherwise); import models; leave calculator method stubs as `raise NotImplementedError` (depends on T010, T011)

**Checkpoint**: Foundation complete — domain models loadable, engine instantiable. All user story phases can now begin.

---

## Phase 3: User Story 1 — Flow Efficiency Monitoring (Priority: P1) 🎯 MVP

**Goal**: Compute and display flow efficiency per workstream; flag below-threshold workstreams;
enable CSV export of the view.

**Independent Test**: Load `tests/fixtures/portfolio_minimal.json` + `tests/fixtures/work_item_events_minimal.csv`
(two workstreams: one at ~38% efficiency, one at ~62%). Run `engine.calculate_flow_efficiency()`.
Verify: (1) the 38%-efficiency workstream has `below_threshold=True`; (2) CSV export produces
`flow_efficiency.csv` with correct rows sorted worst-first; (3) dashboard Tab 1 renders with
the low-efficiency workstream bar in red.

### Implementation for User Story 1

- [X] T013 [P] [US1] Create `tests/fixtures/portfolio_minimal.json` with 2 workstreams (`ws-cloud` at threshold 0.45, `ws-product` at threshold 0.50), 3 teams total (Alpha: $2,500/day, Beta: $3,000/day under ws-cloud; Gamma: $2,800/day under ws-product) — use the exact schema from `contracts/input-schema.md`
- [X] T014 [P] [US1] Create `tests/fixtures/work_item_events_minimal.csv` with 6 work items (4 under ws-cloud teams, 2 under ws-product) using state transitions that produce ~38% flow efficiency for ws-cloud and ~62% for ws-product — include P0, P1, Medium priorities and at least 2 items with `business_value` set
- [X] T015 [US1] Implement `FlowEfficiencyCalculator` in `src/delivery_engine/calculators/flow_efficiency.py`: method `calculate(portfolio: Portfolio, work_items: list[WorkItem]) -> list[FlowEfficiencyResult]`; group WorkItems by workstream; compute `flow_efficiency_pct = (Σ active_time_days / Σ lead_time_days) × 100` per workstream; set `below_threshold = True` if pct < `workstream.flow_efficiency_threshold × 100`; return sorted by `flow_efficiency_pct` ascending; use Polars DataFrame for groupby (depends on T012, T013, T014)
- [X] T016 [US1] Add `calculate_flow_efficiency(self) -> list[FlowEfficiencyResult]` to `DeliveryAnalyticsEngine` in `src/delivery_engine/engine.py`: instantiate `FlowEfficiencyCalculator`, call `calculate()`, return results (depends on T015)
- [X] T017 [US1] Implement `ReportExporter` class in `src/delivery_engine/io/exporter.py` with `export_csv(report, output_dir: str) -> list[str]`; for US1 only implement the `flow_efficiency.csv` writer using columns from `contracts/output-schema.md`; create `output_dir` if it does not exist; return list of written file paths (depends on T016)
- [X] T018 [US1] Implement dashboard Tab 1 in `src/delivery_engine/dashboard/app.py`: `build_flow_efficiency_tab(results: list[FlowEfficiencyResult]) -> dcc.Tab` — horizontal bar chart using `plotly.express.bar(orientation="h")`; below-threshold bars colored red (`#E74C3C`), compliant bars green (`#27AE60`); add a vertical threshold line; hover shows workstream name and exact percentage (depends on T016)

**Checkpoint**: US1 fully functional — `engine.calculate_flow_efficiency()` returns correct results,
`flow_efficiency.csv` is exportable, Tab 1 renders with correct color coding.

---

## Phase 4: User Story 2 — Cost of Delay by Team (Priority: P2)

**Goal**: Compute CoD per team (CoD = wait_time_days × resource_daily_rate), rank teams
by total financial waste, enable ticket-level drill-down, export to CSV.

**Independent Test**: Using `tests/fixtures/portfolio_minimal.json` + `tests/fixtures/work_item_events_minimal.csv`,
verify: Gamma Team's CoD > Alpha Team's CoD (given Gamma's longer wait times in fixture);
`cost_of_delay.csv` rows sorted by team total descending; dashboard Tab 2 bar chart matches
sort order and clicking a team bar expands a ticket breakdown table.

### Implementation for User Story 2

- [X] T019 [US2] Implement `CostOfDelayCalculator` in `src/delivery_engine/calculators/cost_of_delay.py`: method `calculate(portfolio: Portfolio, work_items: list[WorkItem]) -> list[CostOfDelayResult]`; for each WorkItem compute `cost_of_delay = wait_time_days × team.resource_daily_rate`; aggregate per team into `CostOfDelayResult` with `breakdown: list[WorkItemCoDEntry]`; skip teams where `resource_daily_rate is None` (log warning); sort by `total_cost_of_delay` descending; use Polars for aggregation (depends on T012)
- [X] T020 [US2] Add `calculate_cost_of_delay(self) -> list[CostOfDelayResult]` to `DeliveryAnalyticsEngine` in `src/delivery_engine/engine.py` (depends on T019)
- [X] T021 [US2] Add CoD CSV writer to `ReportExporter.export_csv()` in `src/delivery_engine/io/exporter.py`: write `cost_of_delay.csv` with per-ticket rows plus team-total summary rows per `contracts/output-schema.md` column spec (depends on T020)
- [X] T022 [US2] Add Tab 2 to dashboard in `src/delivery_engine/dashboard/app.py`: `build_cost_of_delay_tab(results: list[CostOfDelayResult]) -> dcc.Tab` — vertical bar chart sorted by CoD descending; use Dash callback (`@app.callback`) so clicking a team bar populates a `dcc.DataTable` below the chart with per-ticket breakdown (`title`, `priority`, `wait_time_days`, `resource_daily_rate`, `cost_of_delay` columns) (depends on T020)

**Checkpoint**: US1 and US2 both independently functional — CoD figures accurate, Tab 2 drill-down works.

---

## Phase 5: User Story 3 — Cycle Time Distribution & Predictability (Priority: P3)

**Goal**: Compute median and IQR of cycle time per priority tier for completed WorkItems;
flag high-variance tiers; enable team-level filtering; export to CSV.

**Independent Test**: Using minimal fixtures (ensure at least 4 completed items per priority
tier), verify: cycle time median and IQR are computed correctly per tier; a tier where
IQR > 2 × median has `high_variance=True`; Tab 3 box plot renders; team filter updates
the chart.

### Implementation for User Story 3

- [X] T023 [US3] Implement `CycleTimeAnalyzer` in `src/delivery_engine/calculators/cycle_time.py`: method `analyze(work_items: list[WorkItem], priority_filter: list[str] | None = None) -> list[CycleTimeResult]`; filter to completed WorkItems only (raises `InsufficientDataError` if none); group by `priority`; compute `median_days` and `iqr_days` (P75 − P25) using Polars `quantile()`; set `high_variance = iqr_days > HIGH_VARIANCE_MULTIPLIER × median_days`; sort by `iqr_days` descending (depends on T012)
- [X] T024 [US3] Add `analyze_cycle_time(self, priority_filter=None) -> list[CycleTimeResult]` to `DeliveryAnalyticsEngine` in `src/delivery_engine/engine.py` (depends on T023)
- [X] T025 [US3] Add cycle time CSV writer to `ReportExporter.export_csv()` in `src/delivery_engine/io/exporter.py`: write `cycle_time.csv` per `contracts/output-schema.md` column spec (depends on T024)
- [X] T026 [US3] Add Tab 3 to dashboard in `src/delivery_engine/dashboard/app.py`: `build_cycle_time_tab(results: list[CycleTimeResult], work_items: list[WorkItem]) -> dcc.Tab` — box plot using `plotly.express.box()` grouped by priority; high-variance tiers use `marker_color="#E74C3C"`; add `dcc.Dropdown` for team filter that triggers a Dash callback to recompute and re-render the chart (depends on T024)

**Checkpoint**: US1, US2, and US3 all independently functional — cycle time distributions
visible with variance flagging; team filter working.

---

## Phase 6: User Story 4 — Value vs. Lead Time ROI Analysis (Priority: P4)

**Goal**: Plot each feature by business value (y) vs. lead time (x); enable hover detail
and priority filter; export scatter data to CSV.

**Independent Test**: Using fixtures (ensure at least 5 items with `business_value` set),
verify: all scored items appear in `roi_scatter.csv` with correct coordinates; unscored
items absent; Tab 4 scatter renders; hovering a point shows title, value, lead time;
priority filter limits visible points.

### Implementation for User Story 4

- [X] T027 [US4] Implement `ROIScatterAnalyzer` in `src/delivery_engine/calculators/roi_scatter.py`: method `analyze(portfolio: Portfolio, work_items: list[WorkItem], priority_filter: list[str] | None = None) -> list[ROIScatterPoint]`; exclude WorkItems where `business_value is None`; for each remaining item return `ROIScatterPoint` with `lead_time_days`, `business_value`, `priority`, `title`, `team_name`, `workstream_name`; sort by `business_value` descending (depends on T012)
- [X] T028 [US4] Add `analyze_roi_scatter(self, priority_filter=None) -> list[ROIScatterPoint]` to `DeliveryAnalyticsEngine` in `src/delivery_engine/engine.py` (depends on T027)
- [X] T029 [US4] Add ROI scatter CSV writer to `ReportExporter.export_csv()` in `src/delivery_engine/io/exporter.py`: write `roi_scatter.csv` per `contracts/output-schema.md` column spec (depends on T028)
- [X] T030 [US4] Add Tab 4 to dashboard in `src/delivery_engine/dashboard/app.py`: `build_roi_scatter_tab(points: list[ROIScatterPoint]) -> dcc.Tab` — scatter chart using `plotly.express.scatter(x="lead_time_days", y="business_value", color="priority", hover_data=["title", "business_value", "lead_time_days"])`; add `dcc.Dropdown` for priority filter with Dash callback; use `include_plotlyjs=True` for self-containment (depends on T028)

**Checkpoint**: All 4 user stories independently functional — ROI scatter visible with
hover and filter; all 4 CSV exports work.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wire all stories into the unified facade, produce the full self-contained
HTML dashboard, add global filters, and validate performance at scale.

- [X] T031 Implement `calculate_all(self) -> EngineReport` in `src/delivery_engine/engine.py`: call all four calculators, build `ReportSummary` (total CoD, worst efficiency workstream, highest CoD team, most variable priority tier, item/team/workstream counts), return `EngineReport` dataclass (depends on T016, T020, T024, T028)
- [X] T032 Implement `ReportExporter.export_dashboard(report: EngineReport, output_path: str) -> str` in `src/delivery_engine/io/exporter.py`: build Dash app with all 4 tabs using `build_*_tab()` functions from `src/delivery_engine/dashboard/app.py`; add header strip with 4 KPI metrics (total CoD, worst workstream, highest CoD team, most variable tier); call `app.write_html(output_path, include_plotlyjs=True)` — NOT `"cdn"`; return absolute output path (depends on T031, T018, T022, T026, T030)
- [X] T033 Add global filter bar to dashboard in `src/delivery_engine/dashboard/app.py`: date range picker (`dcc.DatePickerRange`) and workstream multi-select dropdown (`dcc.Dropdown(multi=True)`) that trigger a unified Dash callback refreshing all 4 tabs simultaneously (depends on T032)
- [X] T034 [P] Create `tests/fixtures/portfolio_large.json` with 10 workstreams and 50 teams (5 teams per workstream, varied daily rates $1,500–$4,000) for SC-003 performance validation
- [X] T035 [P] Create `tests/fixtures/work_item_events_large.csv` with 10,000 work item events (approx. 200 items × 5 transitions each) distributed across 50 teams, mixed priorities and business values
- [X] T036 Validate `quickstart.md` Scenario 1–4 end-to-end: load `portfolio_minimal.json` + `work_item_events_minimal.csv`, call `engine.calculate_all()`, call `exporter.export_csv()` and `exporter.export_dashboard()`; confirm output files exist and are non-empty; confirm dashboard HTML is self-contained (no CDN URLs present in file) (depends on T032)
- [X] T037 [P] Update `src/delivery_engine/__init__.py` to export public API: `DeliveryAnalyticsEngine`, `DataLoader`, `ReportExporter`; add module docstring summarising the package
- [X] T038 [P] Add CLI entry point `src/delivery_engine/cli.py` with `main()` function: parse `--portfolio`, `--events`, `--output-dir` args using `argparse`; call `DataLoader`, `DeliveryAnalyticsEngine.calculate_all()`, `ReportExporter.export_csv()` and `export_dashboard()`; print output file paths on success

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on US2/US3/US4
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on US1/US3/US4
- **US3 (Phase 5)**: Depends on Phase 2 — no dependency on US1/US2/US4
- **US4 (Phase 6)**: Depends on Phase 2 — no dependency on US1/US2/US3
- **Polish (Phase 7)**: Depends on all 4 user story phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on other stories
- **US2 (P2)**: Can start after Phase 2 in parallel with US1
- **US3 (P3)**: Can start after Phase 2 in parallel with US1 and US2
- **US4 (P4)**: Can start after Phase 2 in parallel with US1, US2, and US3

### Within Each User Story

- Fixtures (T013, T014) run in parallel, before the calculator
- Calculator (T015, T019, T023, T027) before engine method
- Engine method before exporter and dashboard tab
- Exporter and dashboard tab are independent of each other [P]

---

## Parallel Example: User Story 1

```bash
# Run in parallel — independent files:
Task T013: Create tests/fixtures/portfolio_minimal.json
Task T014: Create tests/fixtures/work_item_events_minimal.csv

# Then sequentially (depends on T013, T014):
Task T015: src/delivery_engine/calculators/flow_efficiency.py
Task T016: src/delivery_engine/engine.py (add calculate_flow_efficiency)

# Then in parallel (both depend on T016, different files):
Task T017: src/delivery_engine/io/exporter.py (flow_efficiency.csv)
Task T018: src/delivery_engine/dashboard/app.py (Tab 1)
```

## Parallel Example: All User Stories (Team of 4)

```bash
# After Phase 2 complete:
Developer A → Phase 3 (US1): T013 → T014 → T015 → T016 → T017 + T018
Developer B → Phase 4 (US2): T019 → T020 → T021 + T022
Developer C → Phase 5 (US3): T023 → T024 → T025 + T026
Developer D → Phase 6 (US4): T027 → T028 → T029 + T030
# All merge → Phase 7 Polish together
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `engine.calculate_flow_efficiency()` returns correct results,
   `flow_efficiency.csv` exports, Tab 1 renders with color-coded bars
5. Demo to stakeholders — this is a shippable increment

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Validate independently → Demo (MVP: flow efficiency dashboard)
3. US2 → Validate independently → Demo (adds CoD ranking + drill-down)
4. US3 → Validate independently → Demo (adds cycle time predictability)
5. US4 → Validate independently → Demo (adds ROI scatter strategic view)
6. Polish → Full `calculate_all()` + unified HTML dashboard + CLI

---

## Notes

- [P] tasks modify different files — safe to run in parallel
- [US?] label maps task to user story for traceability to spec.md
- All 4 user stories are independently testable using the minimal fixtures
- Do not start Phase 7 until all 4 user stories are individually validated
- Commit after each checkpoint (end of each phase)
- Performance validation (T034, T035) deferred to Polish — not needed for story demos
