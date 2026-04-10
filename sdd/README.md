# Portfolio Delivery Governance Engine

A Python analytics engine that processes delivery data and generates an interactive governance dashboard — covering flow efficiency, cost of delay, cycle time distribution, and value vs. lead time.

---

## What it does

Given a flat CSV of work items with dates, the engine:

1. Infers wait / active / completed state transitions from `created_at`, `started_at`, `completed_at`
2. Builds a portfolio structure (workstreams → teams) automatically from the data
3. Runs four analyses: flow efficiency, cost of delay, cycle time, ROI scatter
4. Exports a self-contained `dashboard.html` you can open in any browser — no server required

---

## Dashboard

The output is a single HTML file with four interactive Plotly tabs:

| Tab | Chart | Notes |
|---|---|---|
| Flow Efficiency | Horizontal bar by workstream | Red = below 45% threshold |
| Cost of Delay | Bar chart by team | Click a bar to drill into per-ticket breakdown |
| Cycle Time | Box plot by priority | Red = high variance (IQR > 2× median) |
| ROI Scatter | Scatter: business value vs lead time | Colored by priority |

A KPI header row shows total portfolio CoD, worst workstream, highest CoD team, and most variable priority tier.

---

## Quick start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Run with a flat CSV

```bash
delivery-engine \
  --flat-csv tests/fixtures/strategic_delivery_data.csv \
  --output-dir reports/
```

Or via the module directly:

```bash
python3 -m delivery_engine.cli \
  --flat-csv tests/fixtures/strategic_delivery_data.csv \
  --output-dir reports/
```

### 3. Open the dashboard

```bash
open reports/dashboard.html
```

---

## Input formats

### Flat CSV (recommended)

A single file — no separate portfolio config needed. Required columns:

| Column | Type | Description |
|---|---|---|
| `ticket_id` | string | Unique work item identifier |
| `workstream` | string | Workstream name |
| `team` | string | Team name |
| `priority` | string | `Critical` / `High` / `Medium` / `Low` |
| `business_value_usd` | float | Business value in USD |
| `resource_daily_rate` | float | Team daily cost rate in USD |
| `created_at` | date | When the item entered the queue |
| `started_at` | date | When active work began |
| `completed_at` | date | When the item was delivered |

See `tests/fixtures/strategic_delivery_data.csv` for a working example (59 items across 4 workstreams and 6 teams).

### Standard mode (portfolio.json + events CSV)

For more control — define the portfolio structure explicitly:

```bash
delivery-engine \
  --portfolio path/to/portfolio.json \
  --events path/to/work_item_events.csv \
  --output-dir reports/
```

See `tests/fixtures/portfolio_minimal.json` and `tests/fixtures/work_item_events_minimal.csv` for the expected schemas.

---

## Output files

All written to `--output-dir`:

| File | Contents |
|---|---|
| `dashboard.html` | Self-contained interactive dashboard (open in any browser) |
| `flow_efficiency.csv` | Flow efficiency % per workstream |
| `cost_of_delay.csv` | CoD per team with per-ticket breakdown |
| `cycle_time.csv` | Median, IQR, variance flag per priority tier |
| `roi_scatter.csv` | Business value and lead time per work item |

---

## Project structure

```
src/
  delivery_engine/
    cli.py                  # Entry point
    engine.py               # Orchestrates all calculators
    config.py               # Thresholds and state-type mappings
    io/
      loader.py             # DataLoader (flat CSV + standard mode)
      exporter.py           # CSV and HTML export
    models/
      portfolio.py
      team.py
      workstream.py
      work_item.py
    calculators/
      flow_efficiency.py
      cost_of_delay.py
      cycle_time.py
      roi_scatter.py
    dashboard/
      app.py                # Dash app (interactive server mode)
      static.py             # Self-contained HTML renderer
tests/
  fixtures/                 # Sample data files
  unit/
  integration/
```

---

## Development

```bash
# Run tests
cd src && pytest

# Lint
ruff check .
```

---

## Requirements

- Python 3.12+
- polars >= 0.20
- plotly >= 5.18
- dash >= 2.14
- pydantic >= 2.0
