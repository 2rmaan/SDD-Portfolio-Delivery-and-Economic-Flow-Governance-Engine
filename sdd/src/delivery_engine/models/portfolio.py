from __future__ import annotations

from dataclasses import dataclass, field

from delivery_engine.models.team import Team
from delivery_engine.models.work_item import WorkItem
from delivery_engine.models.workstream import Workstream


@dataclass
class Portfolio:
    id: str
    name: str
    currency: str = "USD"
    workstreams: list[Workstream] = field(default_factory=list)
    _teams: list[Team] = field(default_factory=list, repr=False)
    work_items: list[WorkItem] = field(default_factory=list, repr=False)

    def get_team(self, team_id: str) -> Team | None:
        for team in self._teams:
            if team.id == team_id:
                return team
        return None

    def get_workstream(self, workstream_id: str) -> Workstream | None:
        for ws in self.workstreams:
            if ws.id == workstream_id:
                return ws
        return None

    @property
    def teams(self) -> list[Team]:
        return self._teams

    @teams.setter
    def teams(self, value: list[Team]) -> None:
        self._teams = value
