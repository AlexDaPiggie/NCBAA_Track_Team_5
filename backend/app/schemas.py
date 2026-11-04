"""API request contracts. Responses are plain JSON built in service.py."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Disruption(BaseModel):
    kind: Literal["spike", "delay", "cancel"]
    start_hour: int = Field(ge=0, lt=168, description="hour index in the 7-day window")
    end_hour: int = Field(gt=0, le=168)
    extra_arrivals: float = 0.0     # spike
    shift_hours: int = 3            # delay
    fraction: float = 0.5           # cancel
    note: str = ""


class ScenarioIn(BaseModel):
    name: Literal["ordinary", "low", "medium", "high", "custom"] = "medium"
    custom_intensity: Optional[float] = None
    disruptions: list[Disruption] = []
    parent_id: Optional[str] = None


class PlanIn(BaseModel):
    scenario_id: str
    risk_z: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Shift(BaseModel):
    worker_id: str
    role: Literal["ramp", "fuel", "cs"]
    day: int
    start_hour: int
    end_hour: int
    break_hour: int


class DecisionIn(BaseModel):
    plan_id: str
    action: Literal["approve", "reject", "edit"]
    actor: str = "manager"
    note: str = ""
    shifts: Optional[list[Shift]] = None


class CopilotIn(BaseModel):
    message: str
    scenario_id: Optional[str] = None
    history: list[dict] = []
