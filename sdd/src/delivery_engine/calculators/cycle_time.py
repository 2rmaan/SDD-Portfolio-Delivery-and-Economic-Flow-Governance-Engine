from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from delivery_engine.config import HIGH_VARIANCE_MULTIPLIER
from delivery_engine.models.work_item import WorkItem


@dataclass
class CycleTimeResult:
    priority: str
    median_days: float
    iqr_days: float
    sample_count: int
    high_variance: bool


class InsufficientDataError(Exception):
    """Raised when no completed WorkItems are available for cycle time analysis."""


class CycleTimeAnalyzer:

    def analyze(
        self,
        work_items: list[WorkItem],
        priority_filter: list[str] | None = None,
    ) -> list[CycleTimeResult]:
        completed = [wi for wi in work_items if wi.is_completed]

        if priority_filter:
            completed = [wi for wi in completed if wi.priority in priority_filter]

        if not completed:
            raise InsufficientDataError(
                "No completed WorkItems available for cycle time analysis"
            )

        rows = [
            {"priority": wi.priority, "cycle_time_days": wi.cycle_time_days}
            for wi in completed
        ]
        df = pl.DataFrame(rows)

        results: list[CycleTimeResult] = []
        for (priority,), group in df.group_by(["priority"], maintain_order=False):
            ct = group["cycle_time_days"]
            median = ct.median() or 0.0
            p25 = ct.quantile(0.25, interpolation="linear") or 0.0
            p75 = ct.quantile(0.75, interpolation="linear") or 0.0
            iqr = p75 - p25
            high_variance = iqr > HIGH_VARIANCE_MULTIPLIER * median if median > 0 else False
            results.append(CycleTimeResult(
                priority=str(priority),
                median_days=round(median, 4),
                iqr_days=round(iqr, 4),
                sample_count=len(ct),
                high_variance=high_variance,
            ))

        results.sort(key=lambda r: r.iqr_days, reverse=True)
        return results
