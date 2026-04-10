# Quickstart: Portfolio Delivery & Economic Flow Governance Engine

**Branch**: `001-portfolio-delivery-engine` | **Date**: 2026-04-09

## Prerequisites

```bash
python --version  # must be 3.12+
pip install delivery-engine  # or: pip install -e . from repo root
```

## Minimal Working Example

### Step 1 — Prepare input files

Create `portfolio.json`:

```json
{
  "id": "demo-portfolio",
  "name": "Demo Portfolio",
  "currency": "USD",
  "workstreams": [
    {
      "id": "ws-cloud",
      "name": "Cloud Infrastructure",
      "flow_efficiency_threshold": 0.45,
      "teams": [
        { "id": "team-alpha", "name": "Alpha Team", "resource_daily_rate": 2500.00 },
        { "id": "team-gamma", "name": "Gamma Team", "resource_daily_rate": 2800.00 }
      ]
    }
  ]
}
```

Create `work_item_events.csv`:

```csv
work_item_id,title,priority,business_value,team_id,state,state_type,entered_at,exited_at
WI-001,Deploy Auth,P0,90,team-alpha,Backlog,wait,2026-01-01T08:00:00Z,2026-01-03T09:00:00Z
WI-001,Deploy Auth,P0,90,team-alpha,In Progress,active,2026-01-03T09:00:00Z,2026-01-06T17:00:00Z
WI-001,Deploy Auth,P0,90,team-alpha,Completed,completed,2026-01-06T17:00:00Z,
WI-002,Migrate DB,Medium,,team-gamma,Backlog,wait,2026-01-05T08:00:00Z,2026-01-10T09:00:00Z
WI-002,Migrate DB,Medium,,team-gamma,In Progress,active,2026-01-10T09:00:00Z,2026-01-15T17:00:00Z
WI-002,Migrate DB,Medium,,team-gamma,Blocked,wait,2026-01-15T17:00:00Z,2026-01-22T10:00:00Z
WI-002,Migrate DB,Medium,,team-gamma,In Progress,active,2026-01-22T10:00:00Z,2026-01-24T16:00:00Z
WI-002,Migrate DB,Medium,,team-gamma,Completed,completed,2026-01-24T16:00:00Z,
```

### Step 2 — Run the engine (Python API)

```python
from delivery_engine.io.loader import DataLoader
from delivery_engine.engine import DeliveryAnalyticsEngine
from delivery_engine.io.exporter import ReportExporter

# Load data
portfolio = DataLoader.load_portfolio("portfolio.json")
work_items = DataLoader.load_work_items("work_item_events.csv", portfolio)
portfolio.work_items = work_items

# Compute all metrics
engine = DeliveryAnalyticsEngine(portfolio)
report = engine.calculate_all()

# Export
exporter = ReportExporter()
csv_files = exporter.export_csv(report, output_dir="./output/")
dashboard = exporter.export_dashboard(report, output_path="./output/dashboard.html")

print(f"Dashboard: {dashboard}")
print(f"Highest CoD team: {report.summary.highest_cod_team}")
```

### Step 3 — Open the dashboard

```bash
open ./output/dashboard.html   # macOS
xdg-open ./output/dashboard.html  # Linux
start ./output/dashboard.html  # Windows
```

Expected: Browser opens a 4-tab interactive dashboard. Flow Efficiency tab shows
`Cloud Infrastructure` at ~38% (below the 45% threshold, highlighted in red).

---

## Integration Test Scenarios

### Scenario 1: Flow Efficiency below threshold is flagged (US1 acceptance)

**Setup**: Portfolio with two workstreams. Workstream A has 40% efficiency (below 45%
threshold). Workstream B has 62% efficiency (above 50% threshold).

**Expected**:
- `flow_efficiency.csv` contains two rows
- Workstream A row has `below_threshold = True`, `flow_efficiency_pct ≈ 40.0`
- Workstream B row has `below_threshold = False`
- Dashboard Tab 1 shows Workstream A bar in red

---

### Scenario 2: CoD sorted by highest financial waste (US2 acceptance)

**Setup**: Three teams with known wait times and daily rates:
- Gamma Team: 10 wait days × $2,800/day = $28,000
- Beta Team: 5 wait days × $3,000/day = $15,000
- Alpha Team: 2 wait days × $2,500/day = $5,000

**Expected**:
- `cost_of_delay.csv` team totals ordered: Gamma ($28,000), Beta ($15,000), Alpha ($5,000)
- Dashboard Tab 2 bar chart matches this order
- Clicking Gamma bar expands ticket-level breakdown

---

### Scenario 3: Cycle time variance identified (US3 acceptance)

**Setup**: 20 completed tickets across P0 (tight cycle times: 2–4 days) and Medium
(wide cycle times: 5–30 days).

**Expected**:
- `cycle_time.csv` Medium row has `high_variance = True` (IQR > 2 × median)
- Dashboard Tab 3 box plot shows Medium tier visually wider than P0 tier

---

### Scenario 4: ROI scatter shows high-value/high-delay cluster (US4 acceptance)

**Setup**: 10 features. Features with `business_value > 80` all have `lead_time_days > 20`.
Features with `business_value < 40` all have `lead_time_days < 10`.

**Expected**:
- Dashboard Tab 4 scatter shows a cluster of high-value items at the far right
- `roi_scatter.csv` contains all 10 features with correct coordinates
- Hovering any point shows title, value, and lead time

---

## Edge Case Validation

```python
# WorkItem with no wait time → CoD = 0
assert work_item_no_wait.cost_of_delay == 0.0

# Team with no resource_daily_rate → excluded from CoD, warning logged
# (check logs, not an exception)

# WorkItem with no business_value → absent from ROI scatter
assert work_item_no_value.work_item_id not in [p.work_item_id for p in roi_scatter]

# No completed WorkItems → InsufficientDataError for cycle time only
from delivery_engine.engine import InsufficientDataError
with pytest.raises(InsufficientDataError):
    engine.analyze_cycle_time()
```
