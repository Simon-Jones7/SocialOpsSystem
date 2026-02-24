from typing import Any

from pydantic import BaseModel, Field


class DraftCandidate(BaseModel):
    item_id: str
    platform: str
    format: str
    score: float | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    suggested_schedule_datetime: str | None = None
    blocked: bool = False
    dependency_warnings: list[str] = Field(default_factory=list)


class WeeklyPlanEntry(BaseModel):
    draft_id: str
    platform: str
    scheduled_datetime: str


class ApprovalQueueEntry(BaseModel):
    draft_id: str
    item_id: str
    platform: str
    status: str = "proposed"


class ExportJob(BaseModel):
    draft_id: str
    specs: list[str] = Field(default_factory=list)


class PlannerResult(BaseModel):
    draft_candidates: list[DraftCandidate] = Field(default_factory=list)
    weekly_plan: list[WeeklyPlanEntry] = Field(default_factory=list)
    approval_queue: list[ApprovalQueueEntry] = Field(default_factory=list)
    export_queue: list[ExportJob] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
