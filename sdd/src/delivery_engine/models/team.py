from dataclasses import dataclass


@dataclass
class Team:
    id: str
    name: str
    workstream_id: str
    resource_daily_rate: float | None = None
