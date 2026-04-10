from __future__ import annotations

import json
import logging
from datetime import datetime

import polars as pl
from pydantic import BaseModel, field_validator, model_validator

from delivery_engine.config import STATE_TYPE_MAP
from delivery_engine.models.portfolio import Portfolio
from delivery_engine.models.team import Team
from delivery_engine.models.work_item import StateTransition, WorkItem
from delivery_engine.models.workstream import Workstream

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas for portfolio.json validation
# ---------------------------------------------------------------------------

class TeamSchema(BaseModel):
    id: str
    name: str
    resource_daily_rate: float | None = None

    @field_validator("resource_daily_rate")
    @classmethod
    def rate_must_be_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("resource_daily_rate must be > 0")
        return v


class WorkstreamSchema(BaseModel):
    id: str
    name: str
    flow_efficiency_threshold: float = 0.45
    teams: list[TeamSchema]

    @field_validator("flow_efficiency_threshold")
    @classmethod
    def threshold_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("flow_efficiency_threshold must be between 0.0 and 1.0")
        return v

    @field_validator("teams")
    @classmethod
    def at_least_one_team(cls, v: list[TeamSchema]) -> list[TeamSchema]:
        if not v:
            raise ValueError("Each workstream must have at least one team")
        return v


class PortfolioSchema(BaseModel):
    id: str
    name: str
    currency: str = "USD"
    workstreams: list[WorkstreamSchema]

    @field_validator("workstreams")
    @classmethod
    def at_least_one_workstream(cls, v: list[WorkstreamSchema]) -> list[WorkstreamSchema]:
        if not v:
            raise ValueError("Portfolio must have at least one workstream")
        return v

    @field_validator("currency")
    @classmethod
    def currency_format(cls, v: str) -> str:
        if not v.isalpha() or len(v) != 3:
            raise ValueError("currency must be a 3-letter ISO 4217 code")
        return v.upper()

    @model_validator(mode="after")
    def unique_ids(self) -> "PortfolioSchema":
        ws_ids = [ws.id for ws in self.workstreams]
        if len(ws_ids) != len(set(ws_ids)):
            raise ValueError("Workstream ids must be unique")
        team_ids: list[str] = []
        for ws in self.workstreams:
            team_ids.extend(t.id for t in ws.teams)
        if len(team_ids) != len(set(team_ids)):
            raise ValueError("Team ids must be unique across portfolio")
        return self


def _resolve_state_type(state_label: str) -> str:
    lower = state_label.lower()
    for pattern, state_type in STATE_TYPE_MAP:
        if pattern in lower:
            return state_type
    return "wait"  # default: treat unknown states as wait


class DataLoader:

    @staticmethod
    def load_portfolio(portfolio_json_path: str) -> Portfolio:
        with open(portfolio_json_path, encoding="utf-8") as f:
            raw = json.load(f)

        schema = PortfolioSchema.model_validate(raw)

        teams_all: list[Team] = []
        workstreams: list[Workstream] = []

        for ws_schema in schema.workstreams:
            team_ids: list[str] = []
            for t_schema in ws_schema.teams:
                team = Team(
                    id=t_schema.id,
                    name=t_schema.name,
                    workstream_id=ws_schema.id,
                    resource_daily_rate=t_schema.resource_daily_rate,
                )
                teams_all.append(team)
                team_ids.append(t_schema.id)

            workstreams.append(
                Workstream(
                    id=ws_schema.id,
                    name=ws_schema.name,
                    portfolio_id=schema.id,
                    flow_efficiency_threshold=ws_schema.flow_efficiency_threshold,
                    team_ids=team_ids,
                )
            )

        portfolio = Portfolio(
            id=schema.id,
            name=schema.name,
            currency=schema.currency,
            workstreams=workstreams,
        )
        portfolio.teams = teams_all
        return portfolio

    @staticmethod
    def load_from_flat_csv(csv_path: str) -> tuple[Portfolio, list[WorkItem]]:
        """Load a self-contained flat CSV (ticket_id, workstream, team, priority,
        business_value_usd, resource_daily_rate, created_at, started_at, completed_at)
        and return a fully constructed (Portfolio, work_items) pair.

        State transitions are inferred from the three date columns:
          created_at → started_at  : wait  ("In Queue")
          started_at → completed_at: active ("In Progress")
          completed_at             : completed ("Done")
        """
        df = pl.read_csv(csv_path, null_values=["", "null", "NULL", "None"])

        required = {"ticket_id", "workstream", "team", "priority",
                    "resource_daily_rate", "created_at", "started_at", "completed_at"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Flat CSV missing required columns: {missing}")

        # ── Build Portfolio structure ─────────────────────────────────────
        team_meta: dict[str, dict] = {}
        for row in df.to_dicts():
            team_name = str(row["team"])
            if team_name not in team_meta:
                team_meta[team_name] = {
                    "workstream": str(row["workstream"]),
                    "resource_daily_rate": float(row["resource_daily_rate"]),
                }

        ws_to_teams: dict[str, list[str]] = {}
        for team_name, meta in team_meta.items():
            ws_to_teams.setdefault(meta["workstream"], []).append(team_name)

        workstreams: list[Workstream] = []
        teams_all: list[Team] = []
        for ws_name, team_names in ws_to_teams.items():
            ws_id = ws_name.lower().replace(" ", "_")
            team_ids: list[str] = []
            for team_name in team_names:
                team_id = team_name.lower()
                teams_all.append(Team(
                    id=team_id,
                    name=team_name,
                    workstream_id=ws_id,
                    resource_daily_rate=team_meta[team_name]["resource_daily_rate"],
                ))
                team_ids.append(team_id)
            workstreams.append(Workstream(
                id=ws_id,
                name=ws_name,
                portfolio_id="portfolio-flat",
                flow_efficiency_threshold=0.45,
                team_ids=team_ids,
            ))

        portfolio = Portfolio(
            id="portfolio-flat",
            name="Strategic Delivery Portfolio",
            currency="USD",
            workstreams=workstreams,
        )
        portfolio.teams = teams_all

        # ── Build WorkItems with inferred state transitions ───────────────
        work_items: list[WorkItem] = []
        for row in df.to_dicts():
            ticket_id = str(row["ticket_id"])
            team_id = str(row["team"]).lower()
            priority = str(row["priority"])
            bv_raw = row.get("business_value_usd")
            business_value: float | None = float(bv_raw) if bv_raw is not None else None

            created_at = datetime.fromisoformat(str(row["created_at"])).replace(tzinfo=None)
            started_at = datetime.fromisoformat(str(row["started_at"])).replace(tzinfo=None)
            completed_at = datetime.fromisoformat(str(row["completed_at"])).replace(tzinfo=None)

            work_items.append(WorkItem(
                id=ticket_id,
                title=ticket_id,
                priority=priority,
                team_id=team_id,
                state_transitions=[
                    StateTransition(ticket_id, "In Queue",    "wait",      created_at,   started_at),
                    StateTransition(ticket_id, "In Progress", "active",    started_at,   completed_at),
                    StateTransition(ticket_id, "Done",        "completed", completed_at, None),
                ],
                business_value=business_value,
            ))

        portfolio.work_items = work_items
        return portfolio, work_items

    @staticmethod
    def load_work_items(events_csv_path: str, portfolio: Portfolio) -> list[WorkItem]:
        df = pl.read_csv(events_csv_path, null_values=["", "null", "NULL", "None"])

        required_cols = {
            "work_item_id", "title", "priority", "team_id",
            "state", "state_type", "entered_at",
        }
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        # Validate team_ids
        valid_team_ids = {t.id for t in portfolio.teams}
        csv_team_ids = set(df["team_id"].unique().to_list())
        unknown = csv_team_ids - valid_team_ids
        if unknown:
            raise ReferenceError(
                f"team_id(s) in CSV not found in portfolio: {unknown}"
            )

        work_items: list[WorkItem] = []

        for (work_item_id,), group in df.group_by(["work_item_id"], maintain_order=True):
            # Sort by entered_at within group
            group = group.sort("entered_at")

            rows = group.to_dicts()
            first_row = rows[0]

            business_value_raw = first_row.get("business_value")
            business_value: float | None = None
            if business_value_raw is not None:
                try:
                    business_value = float(business_value_raw)
                except (TypeError, ValueError):
                    business_value = None

            transitions: list[StateTransition] = []
            prev_exited: datetime | None = None

            for i, row in enumerate(rows):
                entered_at = datetime.fromisoformat(str(row["entered_at"]))
                exited_at_raw = row.get("exited_at")
                exited_at: datetime | None = None
                if exited_at_raw is not None:
                    exited_at = datetime.fromisoformat(str(exited_at_raw))

                # Chronology check
                if prev_exited is not None and entered_at < prev_exited:
                    raise ValueError(
                        f"WorkItem {work_item_id}: transition {i} entered_at "
                        f"({entered_at}) is before previous exited_at ({prev_exited})"
                    )
                if exited_at is not None and exited_at < entered_at:
                    raise ValueError(
                        f"WorkItem {work_item_id}: exited_at ({exited_at}) "
                        f"is before entered_at ({entered_at})"
                    )

                state_type = str(row["state_type"]) if row.get("state_type") else _resolve_state_type(str(row["state"]))

                transitions.append(StateTransition(
                    work_item_id=str(work_item_id),
                    state=str(row["state"]),
                    state_type=state_type,
                    entered_at=entered_at,
                    exited_at=exited_at,
                ))
                prev_exited = exited_at

            work_items.append(WorkItem(
                id=str(work_item_id),
                title=str(first_row["title"]),
                priority=str(first_row["priority"]),
                team_id=str(first_row["team_id"]),
                state_transitions=transitions,
                business_value=business_value,
            ))

        return work_items
