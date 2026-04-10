from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StateTransition:
    work_item_id: str
    state: str
    state_type: str  # "active" | "wait" | "completed"
    entered_at: datetime
    exited_at: datetime | None = None

    def duration_days(self, as_of: datetime | None = None) -> float:
        end = self.exited_at or as_of or datetime.now(tz=timezone.utc)
        delta = end - self.entered_at
        return max(delta.total_seconds() / 86400, 0.0)


@dataclass
class WorkItem:
    id: str
    title: str
    priority: str
    team_id: str
    state_transitions: list[StateTransition] = field(default_factory=list)
    business_value: float | None = None

    @property
    def wait_time_days(self) -> float:
        return sum(
            t.duration_days() for t in self.state_transitions if t.state_type == "wait"
        )

    @property
    def active_time_days(self) -> float:
        return sum(
            t.duration_days() for t in self.state_transitions if t.state_type == "active"
        )

    @property
    def is_completed(self) -> bool:
        return any(t.state_type == "completed" for t in self.state_transitions)

    @property
    def lead_time_days(self) -> float:
        if not self.state_transitions:
            return 0.0
        completed = [t for t in self.state_transitions if t.state_type == "completed"]
        if not completed:
            return 0.0
        first_entered = self.state_transitions[0].entered_at
        completed_at = completed[-1].entered_at
        return max((completed_at - first_entered).total_seconds() / 86400, 0.0)

    @property
    def cycle_time_days(self) -> float:
        completed = [t for t in self.state_transitions if t.state_type == "completed"]
        if not completed:
            return 0.0
        active_transitions = [t for t in self.state_transitions if t.state_type == "active"]
        if not active_transitions:
            return 0.0
        first_active_at = active_transitions[0].entered_at
        completed_at = completed[-1].entered_at
        return max((completed_at - first_active_at).total_seconds() / 86400, 0.0)

    def cost_of_delay(self, team_daily_rate: float) -> float:
        return self.wait_time_days * team_daily_rate
