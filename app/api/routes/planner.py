from __future__ import annotations

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from typing import Any

from app.core.config_loader import ConfigLoader
from app.models.planner import PlannerResult
from app.services.planner import run_planner


router = APIRouter(prefix="/planner", tags=["planner"])


class RunPlannerRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    campaigns: list[dict[str, Any]] = Field(default_factory=list)
    objectives: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/run", response_model=PlannerResult)
def run_planner_endpoint(
    payload: RunPlannerRequest = Body(default_factory=RunPlannerRequest),
) -> PlannerResult:
    configs = ConfigLoader().load_all()
    return run_planner(
        items=payload.items,
        campaigns=payload.campaigns,
        objectives=payload.objectives,
        configs=configs,
    )

