from __future__ import annotations

from dataclasses import dataclass

from delivery_engine.models.portfolio import Portfolio
from delivery_engine.models.work_item import WorkItem


@dataclass
class ROIScatterPoint:
    work_item_id: str
    title: str
    priority: str
    business_value: float
    lead_time_days: float
    team_name: str
    workstream_name: str


class ROIScatterAnalyzer:

    def analyze(
        self,
        portfolio: Portfolio,
        work_items: list[WorkItem],
        priority_filter: list[str] | None = None,
    ) -> list[ROIScatterPoint]:
        team_map = {t.id: t for t in portfolio.teams}
        ws_map = {ws.id: ws for ws in portfolio.workstreams}
        team_to_ws: dict[str, str] = {}
        for ws in portfolio.workstreams:
            for tid in ws.team_ids:
                team_to_ws[tid] = ws.id

        points: list[ROIScatterPoint] = []
        for wi in work_items:
            if wi.business_value is None:
                continue
            if priority_filter and wi.priority not in priority_filter:
                continue

            team = team_map.get(wi.team_id)
            team_name = team.name if team else wi.team_id
            ws_id = team_to_ws.get(wi.team_id, "")
            ws = ws_map.get(ws_id)
            ws_name = ws.name if ws else ""

            points.append(ROIScatterPoint(
                work_item_id=wi.id,
                title=wi.title,
                priority=wi.priority,
                business_value=wi.business_value,
                lead_time_days=round(wi.lead_time_days, 4),
                team_name=team_name,
                workstream_name=ws_name,
            ))

        points.sort(key=lambda p: p.business_value, reverse=True)
        return points
