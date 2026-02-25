from datetime import datetime
from typing import Any

from app.models.planner import DraftCandidate, Item, PlannerResult


def _resolve_field_path(item: Item, field_path: str) -> Any:
    # supports paths like "item.links.eventbrite"
    parts = field_path.split(".")
    if not parts or parts[0] != "item":
        return None

    value: Any = item
    for part in parts[1:]:
        if value is None:
            return None
        value = getattr(value, part, None)
    return value


def _check_clause(item: Item, clause: dict[str, Any]) -> bool:
    field = clause.get("field")
    if not field:
        return False

    value = _resolve_field_path(item, field)

    if "exists" in clause:
        exists = bool(clause.get("exists"))
        present = value is not None and value != ""
        return present == exists

    if "gte" in clause:
        try:
            return value is not None and float(value) >= float(clause["gte"])
        except (TypeError, ValueError):
            return False

    return False


def _evaluate_dependencies(
    item: Item,
    platform: str,
    fmt: str,
    dependency_rules: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    for rule in dependency_rules:
        when = rule.get("when") or {}

        when_platform = when.get("platform")
        when_item_type = when.get("item_type")
        when_format = when.get("format")

        if when_platform and when_platform != platform:
            continue
        if when_item_type and when_item_type != item.item_type:
            continue
        if when_format and when_format != fmt:
            continue

        req = rule.get("require") or {}
        all_clauses = req.get("all") or []
        any_clauses = req.get("any") or []

        all_ok = all(_check_clause(item, clause) for clause in all_clauses) if all_clauses else True
        any_ok = any(_check_clause(item, clause) for clause in any_clauses) if any_clauses else True

        if not (all_ok and any_ok):
            on_fail = rule.get("on_fail") or {}
            if on_fail.get("blocked", False):
                return True, on_fail.get("message") or f"Blocked by dependency rule: {rule.get('id', 'unknown')}"

    return False, None


def run_planner(
    *,
    items: list[Item] | None = None,
    campaigns: list[dict[str, Any]] | None = None,
    objectives: list[dict[str, Any]] | None = None,
    configs: dict[str, Any] | None = None,
) -> PlannerResult:
    """Milestone A+B planner scaffold.

    Generates draft candidates and applies dependency gating only.
    Scoring/scheduling/export logic intentionally not implemented.
    """
    items = items or []
    campaigns = campaigns or []
    objectives = objectives or []
    configs = configs or {}

    formats_by_platform: dict[str, list[str]] = (
        ((configs.get("scoring_rules") or {}).get("candidate_generation") or {}).get("formats_by_platform") or {}
    )
    dependency_rules: list[dict[str, Any]] = ((configs.get("dependency_rules") or {}).get("rules") or [])

    draft_candidates: list[DraftCandidate] = []

    for item in items:
        for platform, formats in formats_by_platform.items():
            for fmt in formats:
                blocked, block_reason = _evaluate_dependencies(item, platform, fmt, dependency_rules)
                draft_candidates.append(
                    DraftCandidate(
                        item_id=item.id,
                        platform=platform,
                        format=fmt,
                        blocked=blocked,
                        block_reason=block_reason,
                    )
                )

    blocked_count = sum(1 for c in draft_candidates if c.blocked)
    total_count = len(draft_candidates)

    return PlannerResult(
        draft_candidates=draft_candidates,
        weekly_plan=[],
        approval_queue=[],
        export_queue=[],
        metadata={
            "status": "milestone_ab",
            "message": "Candidate generation and dependency gating implemented. Scoring/scheduling not implemented yet.",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_counts": {
                "items": len(items),
                "campaigns": len(campaigns),
                "objectives": len(objectives),
                "config_files": len(configs),
            },
            "total_candidates": total_count,
            "blocked_candidates": blocked_count,
            "unblocked_candidates": total_count - blocked_count,
            "validation_status": "passed",
        },
    )