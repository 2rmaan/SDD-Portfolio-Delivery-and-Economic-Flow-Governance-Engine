# Contract: DeliveryAnalyticsEngine Python API

**Type**: Python class interface (library contract)
**Produced by**: Phase 1 Design

---

## DeliveryAnalyticsEngine (Facade)

Primary entry point. All metric computation passes through this class.

```python
class DeliveryAnalyticsEngine:

    def __init__(self, portfolio: Portfolio) -> None:
        """
        Initialize the engine with a loaded Portfolio domain object.
        The Portfolio must contain at least one Workstream with at least one Team.
        Raises: ValueError if portfolio has no workstreams.
        """

    def calculate_flow_efficiency(self) -> list[FlowEfficiencyResult]:
        """
        Compute flow efficiency for every workstream in the portfolio.

        Returns:
            List of FlowEfficiencyResult, one per workstream, sorted by
            efficiency ascending (worst first).

        Raises:
            EngineError if no WorkItems exist across the portfolio.
        """

    def calculate_cost_of_delay(self) -> list[CostOfDelayResult]:
        """
        Compute total Cost of Delay per team, sorted by CoD descending.
        CoD per WorkItem = wait_time_days × team.resource_daily_rate.
        Teams with no resource_daily_rate are excluded; a warning is logged.

        Returns:
            List of CostOfDelayResult, one per team with a valid daily rate,
            sorted by total_cost_of_delay descending.
        """

    def analyze_cycle_time(
        self,
        priority_filter: list[str] | None = None
    ) -> list[CycleTimeResult]:
        """
        Compute cycle time distribution (median + IQR) per priority tier,
        for completed WorkItems only.

        Args:
            priority_filter: If provided, limit results to these priority labels.

        Returns:
            List of CycleTimeResult, one per priority tier present in the data.

        Raises:
            EngineError if no completed WorkItems exist.
        """

    def analyze_roi_scatter(
        self,
        priority_filter: list[str] | None = None
    ) -> list[ROIScatterPoint]:
        """
        Produce lead time vs. business value data points for the scatter chart.
        WorkItems with no business_value are excluded.

        Args:
            priority_filter: If provided, limit results to these priority labels.

        Returns:
            List of ROIScatterPoint, one per qualifying WorkItem.
        """

    def calculate_all(self) -> EngineReport:
        """
        Run all four calculators and return a combined report.

        Returns:
            EngineReport containing all four result sets plus summary statistics.
        """
```

---

## Result Types

```python
@dataclass
class FlowEfficiencyResult:
    workstream_id: str
    workstream_name: str
    flow_efficiency_pct: float        # 0.0–100.0
    active_time_days: float
    total_lead_time_days: float
    below_threshold: bool             # True if < threshold (default 45%)
    threshold_pct: float              # The configured threshold

@dataclass
class CostOfDelayResult:
    team_id: str
    team_name: str
    workstream_name: str
    total_cost_of_delay: float        # In portfolio currency
    work_item_count: int
    breakdown: list[WorkItemCoDEntry] # Per-ticket detail

@dataclass
class WorkItemCoDEntry:
    work_item_id: str
    title: str
    priority: str
    wait_time_days: float
    resource_daily_rate: float
    cost_of_delay: float

@dataclass
class CycleTimeResult:
    priority: str
    median_days: float
    iqr_days: float                   # Interquartile range (spread measure)
    sample_count: int
    high_variance: bool               # True if IQR > 2 × median

@dataclass
class ROIScatterPoint:
    work_item_id: str
    title: str
    priority: str
    business_value: float             # 0.0–100.0
    lead_time_days: float
    team_name: str
    workstream_name: str

@dataclass
class EngineReport:
    portfolio_name: str
    generated_at: datetime
    flow_efficiency: list[FlowEfficiencyResult]
    cost_of_delay: list[CostOfDelayResult]
    cycle_time: list[CycleTimeResult]
    roi_scatter: list[ROIScatterPoint]
    summary: ReportSummary

@dataclass
class ReportSummary:
    total_portfolio_cod: float
    worst_flow_efficiency_workstream: str
    highest_cod_team: str
    most_variable_priority_tier: str
    work_item_count: int
    team_count: int
    workstream_count: int
```

---

## DataLoader Contract

```python
class DataLoader:

    @staticmethod
    def load_portfolio(portfolio_json_path: str) -> Portfolio:
        """
        Load and validate portfolio.json.
        Raises: ValidationError (Pydantic) on schema violations.
        Raises: FileNotFoundError if path does not exist.
        """

    @staticmethod
    def load_work_items(events_csv_path: str, portfolio: Portfolio) -> list[WorkItem]:
        """
        Load work_item_events.csv and materialize WorkItem domain objects.
        Aggregates multiple event rows per work_item_id into StateTransition lists.
        Raises: ValidationError on schema violations.
        Raises: ReferenceError if team_id in CSV does not exist in portfolio.
        """
```

---

## ReportExporter Contract

```python
class ReportExporter:

    def export_csv(self, report: EngineReport, output_dir: str) -> list[str]:
        """
        Write one CSV file per metric view to output_dir.
        Returns: List of file paths written.
        Files: flow_efficiency.csv, cost_of_delay.csv,
               cycle_time.csv, roi_scatter.csv
        """

    def export_dashboard(self, report: EngineReport, output_path: str) -> str:
        """
        Generate a standalone interactive HTML dashboard (Plotly Dash).
        Returns: Absolute path to the written HTML file.
        The file is self-contained; no server or internet required to view.
        """
```

---

## Error Types

```python
class EngineError(Exception):
    """Base exception for all engine computation errors."""

class ValidationError(EngineError):
    """Raised when input data fails schema validation."""

class InsufficientDataError(EngineError):
    """Raised when a metric cannot be computed due to missing data
    (e.g., no completed WorkItems for cycle time analysis)."""
```
