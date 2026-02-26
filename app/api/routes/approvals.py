from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.approvals_store import set_approval, get_all_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalSetRequest(BaseModel):
    draft_id: str
    status: str
    note: Optional[str] = None


@router.post("/set")
def set_approval_endpoint(payload: ApprovalSetRequest):
    if payload.status not in {"approved", "rejected", "proposed"}:
        return {"error": "Invalid status"}

    set_approval(
        draft_id=payload.draft_id,
        status=payload.status,
        note=payload.note,
    )

    return {"status": "ok"}


@router.get("/list")
def list_approvals():
    return get_all_approvals()