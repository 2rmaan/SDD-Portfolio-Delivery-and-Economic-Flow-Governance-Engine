from dataclasses import dataclass, field


@dataclass
class Workstream:
    id: str
    name: str
    portfolio_id: str
    flow_efficiency_threshold: float = 0.45
    team_ids: list[str] = field(default_factory=list)
