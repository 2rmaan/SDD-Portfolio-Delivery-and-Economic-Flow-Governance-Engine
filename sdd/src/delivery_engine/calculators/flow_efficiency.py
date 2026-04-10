from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from delivery_engine.models.portfolio import Portfolio
from delivery_engine.models.work_item import WorkItem


@dataclass
class FlowEfficiencyResult:
    workstream_id: str
    workstream_name: str
    flow_efficiency_pct: float
    active_time_days: float
    total_lead_time_days: float
    below_threshold: bool
    threshold_pct: float


class FlowEfficiencyCalculator:

    def calculate(
        self,
        portfolio: Portfolio,
        work_items: list[WorkItem],
    ) -> list[FlowEfficiencyResult]:
        # Build team_id → workstream_id lookup
        team_to_ws: dict[str, str] = {}
        for ws in portfolio.workstreams:
            for team_id in ws.team_ids:
                team_to_ws[team_id] = ws.id

        rows = [
            {
                "workstream_id": team_to_ws.get(wi.team_id, "unknown"),
                "active_time_days": wi.active_time_days,
                "lead_time_days": wi.lead_time_days,
            }
            for wi in work_items
            if wi.team_id in team_to_ws
        ]

        if not rows:
            return []

        df = pl.DataFrame(rows)

        agg = df.group_by("workstream_id").agg([
            pl.col("active_time_days").sum().alias("active_time_days"),
            pl.col("lead_time_days").sum().alias("total_lead_time_days"),
        ])

        results: list[FlowEfficiencyResult] = []
        for row in agg.to_dicts():
            ws_id = row["workstream_id"]
            ws = portfolio.get_workstream(ws_id)
            if ws is None:
                continue

            active = row["active_time_days"]
            lead = row["total_lead_time_days"]
            pct = (active / lead * 100) if lead > 0 else 0.0
            threshold_pct = ws.flow_efficiency_threshold * 100

            results.append(FlowEfficiencyResult(
                workstream_id=ws_id,
                workstream_name=ws.name,
                flow_efficiency_pct=round(pct, 2),
                active_time_days=round(active, 4),
                total_lead_time_days=round(lead, 4),
                below_threshold=pct < threshold_pct,
                threshold_pct=threshold_pct,
            ))

        results.sort(key=lambda r: r.flow_efficiency_pct)
        return results
