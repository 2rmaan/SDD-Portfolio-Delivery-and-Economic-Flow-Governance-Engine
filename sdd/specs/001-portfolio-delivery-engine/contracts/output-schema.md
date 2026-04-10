# Contract: Output Schema

**Type**: File-based output (CSV + HTML)
**Version**: v1

---

## CSV Exports

Four CSV files are produced by `ReportExporter.export_csv()`, one per metric view.

### 1. `flow_efficiency.csv`

| Column | Type | Description |
|--------|------|-------------|
| `workstream_id` | string | Workstream identifier |
| `workstream_name` | string | Human-readable name |
| `flow_efficiency_pct` | float | 0.0–100.0; active / lead time × 100 |
| `active_time_days` | float | Total active work time across all WorkItems |
| `total_lead_time_days` | float | Total lead time across all WorkItems |
| `below_threshold` | boolean | True if below configured threshold |
| `threshold_pct` | float | The configured threshold (e.g., 45.0) |

**Sort order**: `flow_efficiency_pct` ascending (worst first)

### Example rows

```csv
workstream_id,workstream_name,flow_efficiency_pct,active_time_days,total_lead_time_days,below_threshold,threshold_pct
ws-cloud,Cloud Infrastructure,38.2,19.1,50.0,True,45.0
ws-product,Product Engineering,61.5,31.5,51.2,False,50.0
```

---

### 2. `cost_of_delay.csv`

One row per work item (enables drill-down). Aggregate team totals are in a separate
summary section at the bottom (rows with blank `work_item_id`).

| Column | Type | Description |
|--------|------|-------------|
| `team_id` | string | Team identifier |
| `team_name` | string | Human-readable name |
| `workstream_name` | string | Parent workstream name |
| `work_item_id` | string | WorkItem identifier (blank for team total rows) |
| `title` | string | WorkItem title (blank for team total rows) |
| `priority` | string | WorkItem priority (blank for team total rows) |
| `wait_time_days` | float | Days in wait states |
| `resource_daily_rate` | float | Team daily rate in portfolio currency |
| `cost_of_delay` | float | wait_time_days × resource_daily_rate |

**Sort order**: By team total `cost_of_delay` descending, team total rows last.

---

### 3. `cycle_time.csv`

| Column | Type | Description |
|--------|------|-------------|
| `priority` | string | Priority tier label |
| `median_days` | float | Median cycle time in days |
| `iqr_days` | float | Interquartile range (P75 − P25) in days |
| `high_variance` | boolean | True if IQR > 2 × median |
| `sample_count` | int | Number of completed WorkItems in this tier |

**Sort order**: By `iqr_days` descending (most variable first)

---

### 4. `roi_scatter.csv`

| Column | Type | Description |
|--------|------|-------------|
| `work_item_id` | string | WorkItem identifier |
| `title` | string | Human-readable name |
| `priority` | string | Priority tier |
| `business_value` | float | 0.0–100.0 |
| `lead_time_days` | float | Days from first state to completed |
| `team_name` | string | Owning team |
| `workstream_name` | string | Parent workstream |

**Sort order**: By `business_value` descending, then `lead_time_days` ascending

---

## HTML Dashboard

Produced by `ReportExporter.export_dashboard()` as a single self-contained HTML file.

### Structure

```
Dashboard
├── Header: Portfolio name, generated timestamp, summary KPIs
│   ├── Total Portfolio CoD (currency)
│   ├── Worst Flow Efficiency Workstream (name + %)
│   ├── Highest CoD Team (name + amount)
│   └── Most Variable Priority Tier (name + IQR)
├── Tab 1: Flow Efficiency by Workstream
│   └── Horizontal bar chart; below-threshold bars in red, compliant in green
├── Tab 2: Cost of Delay by Team
│   └── Vertical bar chart sorted by CoD descending; click bar → drill-down table
├── Tab 3: Cycle Time Distribution
│   └── Box plot per priority tier; high-variance tiers highlighted
└── Tab 4: Value vs. Lead Time Scatter
    └── Scatter chart; x = lead_time_days, y = business_value;
        color-coded by priority; hover shows title, value, lead time
```

### Interactivity Requirements

| View | Required Interaction |
|------|---------------------|
| All tabs | Filter by time period (date range picker) |
| All tabs | Filter by workstream (multi-select dropdown) |
| Flow Efficiency | Hover shows exact %, threshold line displayed |
| CoD by Team | Click team bar → expand per-ticket breakdown table |
| Cycle Time | Filter by team; hover shows sample count |
| ROI Scatter | Hover shows work item title, value, lead time; filter by priority |

### Self-Containment Guarantee

The HTML file MUST be viewable by opening it directly in a browser with no internet
connection and no local server. All JavaScript, CSS, and chart data MUST be embedded
inline. Plotly's `include_plotlyjs="cdn"` is NOT acceptable; use `include_plotlyjs=True`.
