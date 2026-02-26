from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ItemLinks(BaseModel):
    eventbrite: str | None = None


class ItemAssets(BaseModel):
    photo_count: int = 0
    video_count: int = 0


class Item(BaseModel):
    id: str
    item_type: str
    audiences: list[str] = Field(default_factory=list)
    event_start: datetime | None = None
    series_id: str | None = None
    push_level: str | None = None
    links: ItemLinks = Field(default_factory=ItemLinks)
    assets: ItemAssets = Field(default_factory=ItemAssets)


class DraftCandidate(BaseModel):
    item_id: str
    platform: str
    format: str
    blocked: bool = False
    block_reason: str | None = None
    score: float | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    suggested_schedule_datetime: str | None = None
    dependency_warnings: list[str] = Field(default_factory=list)


class WeeklyPlanEntry(BaseModel):
    draft_id: str
    platform: str
    scheduled_datetime: str


class ApprovalQueueEntry(BaseModel):
    draft_id: str
    item_id: str
    platform: str
    scheduled_datetime: str | None = None
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