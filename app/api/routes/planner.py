from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config_loader import ConfigLoader
from app.models.planner import Item, PlannerResult
from app.services.planner import run_planner

router = APIRouter(prefix="/planner", tags=["planner"])


class RunPlannerRequest(BaseModel):
    items: list[Item] = Field(default_factory=list)
    campaigns: list[dict] = Field(default_factory=list)
    objectives: list[dict] = Field(default_factory=list)


@router.post("/run", response_model=PlannerResult)
def run_planner_endpoint(payload: RunPlannerRequest) -> PlannerResult:
    configs = ConfigLoader().load_all()
    return run_planner(
        items=payload.items,
        campaigns=payload.campaigns,
        objectives=payload.objectives,
        configs=configs,
    )
