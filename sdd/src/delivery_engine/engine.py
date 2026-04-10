from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from delivery_engine.calculators.cost_of_delay import (
    CostOfDelayCalculator,
    CostOfDelayResult,
)
from delivery_engine.calculators.cycle_time import (
    CycleTimeAnalyzer,
    CycleTimeResult,
    InsufficientDataError,
)
from delivery_engine.calculators.flow_efficiency import (
    FlowEfficiencyCalculator,
    FlowEfficiencyResult,
)
from delivery_engine.calculators.roi_scatter import (
    ROIScatterAnalyzer,
    ROIScatterPoint,
)
from delivery_engine.models.portfolio import Portfolio


class EngineError(Exception):
    """Base exception for all engine computation errors."""


class ValidationError(EngineError):
    """Raised when input data fails schema validation."""


@dataclass
class ReportSummary:
    total_portfolio_cod: float
    worst_flow_efficiency_workstream: str
    highest_cod_team: str
    most_variable_priority_tier: str
    work_item_count: int
    team_count: int
    workstream_count: int


@dataclass
class EngineReport:
    portfolio_name: str
    generated_at: datetime
    flow_efficiency: list[FlowEfficiencyResult] = field(default_factory=list)
    cost_of_delay: list[CostOfDelayResult] = field(default_factory=list)
    cycle_time: list[CycleTimeResult] = field(default_factory=list)
    roi_scatter: list[ROIScatterPoint] = field(default_factory=list)
    summary: ReportSummary | None = None


class DeliveryAnalyticsEngine:

    def __init__(self, portfolio: Portfolio) -> None:
        if not portfolio.workstreams:
            raise ValueError("Portfolio must contain at least one workstream")
        self._portfolio = portfolio

    def calculate_flow_efficiency(self) -> list[FlowEfficiencyResult]:
        if not self._portfolio.work_items:
            raise EngineError("No WorkItems loaded into portfolio")
        return FlowEfficiencyCalculator().calculate(
            self._portfolio, self._portfolio.work_items
        )

    def calculate_cost_of_delay(self) -> list[CostOfDelayResult]:
        return CostOfDelayCalculator().calculate(
            self._portfolio, self._portfolio.work_items
        )

    def analyze_cycle_time(
        self,
        priority_filter: list[str] | None = None,
    ) -> list[CycleTimeResult]:
        return CycleTimeAnalyzer().analyze(
            self._portfolio.work_items, priority_filter=priority_filter
        )

    def analyze_roi_scatter(
        self,
        priority_filter: list[str] | None = None,
    ) -> list[ROIScatterPoint]:
        return ROIScatterAnalyzer().analyze(
            self._portfolio, self._portfolio.work_items, priority_filter=priority_filter
        )

    def calculate_all(self) -> EngineReport:
        fe = self.calculate_flow_efficiency()
        cod = self.calculate_cost_of_delay()

        try:
            ct = self.analyze_cycle_time()
        except InsufficientDataError:
            ct = []

        roi = self.analyze_roi_scatter()

        total_cod = sum(r.total_cost_of_delay for r in cod)
        worst_ws = fe[0].workstream_name if fe else "N/A"
        highest_cod_team = cod[0].team_name if cod else "N/A"
        most_variable = ct[0].priority if ct else "N/A"

        summary = ReportSummary(
            total_portfolio_cod=total_cod,
            worst_flow_efficiency_workstream=worst_ws,
            highest_cod_team=highest_cod_team,
            most_variable_priority_tier=most_variable,
            work_item_count=len(self._portfolio.work_items),
            team_count=len(self._portfolio.teams),
            workstream_count=len(self._portfolio.workstreams),
        )

        return EngineReport(
            portfolio_name=self._portfolio.name,
            generated_at=datetime.now(tz=timezone.utc),
            flow_efficiency=fe,
            cost_of_delay=cod,
            cycle_time=ct,
            roi_scatter=roi,
            summary=summary,
        )
