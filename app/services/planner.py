from datetime import datetime
from typing import Any

from app.models.planner import PlannerResult


def run_planner(*, items: list[dict[str, Any]] | None = None, campaigns: list[dict[str, Any]] | None = None, objectives: list[dict[str, Any]] | None = None, configs: dict[str, Any] | None = None) -> PlannerResult:
    """Placeholder planner entrypoint.

    This intentionally does not implement scoring/scheduling logic yet.
    It returns the expected envelope so the API and worker can integrate safely.
    """
    return PlannerResult(
        draft_candidates=[],
        weekly_plan=[],
        approval_queue=[],
        export_queue=[],
        metadata={
            "status": "placeholder",
            "message": "Planner skeleton ready. Scoring not implemented yet.",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_counts": {
                "items": len(items or []),
                "campaigns": len(campaigns or []),
                "objectives": len(objectives or []),
                "config_files": len(configs or {}),
            },
        },
    )
