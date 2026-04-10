from __future__ import annotations

import logging
from dataclasses import dataclass, field

import polars as pl

from delivery_engine.models.portfolio import Portfolio
from delivery_engine.models.work_item import WorkItem

logger = logging.getLogger(__name__)


@dataclass
class WorkItemCoDEntry:
    work_item_id: str
    title: str
    priority: str
    wait_time_days: float
    resource_daily_rate: float
    cost_of_delay: float


@dataclass
class CostOfDelayResult:
    team_id: str
    team_name: str
    workstream_name: str
    total_cost_of_delay: float
    work_item_count: int
    breakdown: list[WorkItemCoDEntry] = field(default_factory=list)


class CostOfDelayCalculator:

    def calculate(
        self,
        portfolio: Portfolio,
        work_items: list[WorkItem],
    ) -> list[CostOfDelayResult]:
        # Build lookups
        team_map = {t.id: t for t in portfolio.teams}
        ws_map = {ws.id: ws for ws in portfolio.workstreams}
        team_to_ws = {}
        for ws in portfolio.workstreams:
            for tid in ws.team_ids:
                team_to_ws[tid] = ws.id

        rows = []
        for wi in work_items:
            team = team_map.get(wi.team_id)
            if team is None:
                continue
            if team.resource_daily_rate is None:
                logger.warning(
                    "Team %s (%s) has no resource_daily_rate — excluded from CoD",
                    team.id, team.name,
                )
                continue
            ws_id = team_to_ws.get(wi.team_id, "")
            ws = ws_map.get(ws_id)
            ws_name = ws.name if ws else ""
            cod = wi.wait_time_days * team.resource_daily_rate
            rows.append({
                "team_id": team.id,
                "team_name": team.name,
                "workstream_name": ws_name,
                "work_item_id": wi.id,
                "title": wi.title,
                "priority": wi.priority,
                "wait_time_days": wi.wait_time_days,
                "resource_daily_rate": team.resource_daily_rate,
                "cost_of_delay": cod,
            })

        if not rows:
            return []

        df = pl.DataFrame(rows)

        team_totals = (
            df.group_by(["team_id", "team_name", "workstream_name"])
            .agg(pl.col("cost_of_delay").sum().alias("total_cost_of_delay"))
            .sort("total_cost_of_delay", descending=True)
        )

        results: list[CostOfDelayResult] = []
        for tot_row in team_totals.to_dicts():
            tid = tot_row["team_id"]
            team_rows = df.filter(pl.col("team_id") == tid).to_dicts()
            breakdown = [
                WorkItemCoDEntry(
                    work_item_id=r["work_item_id"],
                    title=r["title"],
                    priority=r["priority"],
                    wait_time_days=r["wait_time_days"],
                    resource_daily_rate=r["resource_daily_rate"],
                    cost_of_delay=r["cost_of_delay"],
                )
                for r in team_rows
            ]
            results.append(CostOfDelayResult(
                team_id=tid,
                team_name=tot_row["team_name"],
                workstream_name=tot_row["workstream_name"],
                total_cost_of_delay=tot_row["total_cost_of_delay"],
                work_item_count=len(breakdown),
                breakdown=breakdown,
            ))

        return results
