# Portfolio Delivery & Economic Flow Governance Engine (SDD)
### Spec-Driven Enterprise Analytics for Multi-Workstream Software Delivery

## Executive Overview

In portfolio delivery, "getting things done" is meaningless without understanding **what it costs** and **where the system leaks value**. This engine was purpose-built to give portfolio managers, delivery leads, and executives a single source of truth for delivery health, grounded in economic reality rather than vanity metrics.

Unlike traditional approaches that calculate metrics in a monolithic script, this implementation was built using **Spec-Driven Development (SDD)** via [GitHub Spec Kit](https://github.com/github/spec-kit). Every line of code traces back to a user story, a functional requirement, and a ratified project constitution. The result is a modular, testable, and extensible analytics engine designed for portfolios with up to **10,000 work items across 50 teams and 10 workstreams**.

---

## How It Was Built: The SDD Approach

This project followed a formal specification-first workflow. The full specification artifacts live in `specs/001-portfolio-delivery-engine/` and were created before any code was written:

| Phase | Artifact | Purpose |
| :--- | :--- | :--- |
| **Constitution** | `constitution.md` | 5 non-negotiable development principles governing all project decisions |
| **Specification** | `spec.md` | 4 user stories with acceptance scenarios, 10 functional requirements, 5 success criteria |
| **Research** | `research.md` | 8 technology decisions with rationale and rejected alternatives |
| **Planning** | `plan.md` | Architecture design, metric formulas, constitution compliance gate |
| **Data Model** | `data-model.md` | Entity definitions: Portfolio, Workstream, Team, WorkItem, StateTransition |
| **Contracts** | `contracts/` | Python API interface, input schema (JSON + CSV), output schema (HTML + CSV) |
| **Tasks** | `tasks.md` | 38 implementation tasks across 5 phases, dependency-ordered by user story |

---

## Key Strategic Metrics

| Metric | Business Significance | How It's Calculated |
| :--- | :--- | :--- |
| **Flow Efficiency** | Reveals the percentage of time work is actively progressing vs. sitting idle in queues. A workstream below 45% is bleeding capital through systemic wait states. | `(Sum of active_time_days / Sum of lead_time_days) x 100` per workstream. Configurable threshold per workstream (default: 45%). |
| **Cost of Delay (CoD)** | Converts abstract "delay" into a dollar figure. Every day a ticket sits in a wait state, the organization pays its resource daily rate for zero value delivered. | `wait_time_days x resource_daily_rate` per ticket, aggregated per team. Drill-down to individual ticket contributions. |
| **Cycle Time Distribution** | Measures delivery predictability. High variance in a priority tier means roadmap commitments are unreliable and planning is guesswork. | Median and IQR (interquartile range) per priority tier. High variance flagged when `IQR > 2 x median`. |
| **Value vs. Lead Time** | Exposes the strategic failure of high-value features taking the longest to reach customers. If the most valuable items cluster at the far right of the lead time axis, the delivery system is inverted. | Scatter plot: x = `lead_time_days`, y = `business_value` per work item, sized by story points, colored by priority. |

---

## Architecture

The engine uses a **Facade + Calculator** pattern for clean separation of concerns:

```
DeliveryAnalyticsEngine (Facade)
    |
    |--- FlowEfficiencyCalculator    (User Story 1)
    |--- CostOfDelayCalculator       (User Story 2)
    |--- CycleTimeAnalyzer           (User Story 3)
    |--- ROIScatterAnalyzer          (User Story 4)
    |
DataLoader (JSON + CSV input)
ReportExporter (CSV + HTML output)
DashApp (Interactive Plotly Dashboard)
```

Each calculator is independently testable, modifiable, and extensible without touching other components.

### Project Structure

```
src/delivery_engine/
    engine.py               # Facade: single entry point for all metrics
    config.py               # Thresholds, state mappings, defaults
    cli.py                  # Command-line interface
    models/
        portfolio.py        # Portfolio (top-level container)
        workstream.py       # Workstream (logical team grouping)
        team.py             # Team with resource daily rate
        work_item.py        # WorkItem + StateTransition with computed properties
    calculators/
        flow_efficiency.py  # US1: Flow Efficiency per workstream
        cost_of_delay.py    # US2: CoD per team with ticket-level breakdown
        cycle_time.py       # US3: Median, IQR, variance flags per priority
        roi_scatter.py      # US4: Value vs. lead time scatter data
    io/
        loader.py           # Ingests portfolio.json + work_item_events.csv
        exporter.py         # Exports to CSV files + HTML dashboard
    dashboard/
        app.py              # Plotly Dash interactive dashboard
        static.py           # Static HTML export
```

---

## Technology Stack

| Component | Choice | Why |
| :--- | :--- | :--- |
| **Language** | Python 3.12 | 5-10% performance gains over 3.11; LTS through 2028 |
| **Data Processing** | Polars | 10-50x faster than pandas for groupby aggregations at 10k-item scale |
| **Visualization** | Plotly + Dash | Native hover interactivity, tabbed dashboard, self-contained HTML output |
| **Validation** | Pydantic v2 | Schema validation at the data boundary with structured error messages |
| **Domain Models** | Python dataclasses | Lightweight OOP with computed properties for all time/cost metrics |
| **Testing** | pytest + pytest-benchmark | Fixture-based tests + performance validation at 10k scale |

---

## SDD Governance

This project is governed by a ratified **Constitution** (`specs/.specify/memory/constitution.md`) with five core principles:

1. **Spec-First Development** - No implementation without a passing spec
2. **User-Story-Centric Design** - Every feature decomposed into independent, testable stories
3. **Constitution-Gated Planning** - Compliance checked at plan-time, not post-hoc
4. **Phase-Validated Execution** - Setup, Foundational, Stories, Polish; each phase gated before the next
5. **Simplicity & Minimalism** - YAGNI by default; complexity must be justified in writing

Any modification to the codebase should follow the SDD workflow: `/speckit.specify` then `/speckit.plan` then `/speckit.tasks` then `/speckit.implement`.
