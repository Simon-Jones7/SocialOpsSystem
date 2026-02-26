from datetime import datetime, timedelta
from typing import Any

from app.models.planner import DraftCandidate, Item, PlannerResult

from app.services.approvals_store import get_all_approvals


def _next_monday(d: datetime) -> datetime:
    # Monday = 0
    days_ahead = (0 - d.weekday()) % 7
    return (d + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)


def _iter_mondays(start: datetime, end: datetime) -> list[datetime]:
    mondays: list[datetime] = []
    cur = _next_monday(start)
    while cur <= end:
        mondays.append(cur)
        cur = cur + timedelta(days=7)
    return mondays


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


# ======================
# Pass 1 Scoring Helpers
# ======================

from datetime import timezone


def _parse_objective_weights(objectives):
    out = {}
    for obj in objectives or []:
        key = (obj.get("id") or obj.get("name") or "").strip()
        if not key:
            continue
        try:
            out[key] = float(obj.get("weight", 0))
        except (TypeError, ValueError):
            out[key] = 0.0
    return out


def _pick_primary_objective(item):
    t = (item.item_type or "").lower()
    if t in {"youtube_upload", "youtube"}:
        return "youtube_growth"
    if t in {"event", "event_promo", "meetup"}:
        return "event_attendance"
    if t in {"deadline", "callout_deadline", "submission_deadline"}:
        return "submission_deadline"
    if t in {"news", "major_news"}:
        return "community_engagement"
    if t in {"bts", "behind_the_scenes", "update"}:
        return "community_engagement"
    return None

def _map_item_type_to_fit_key(item_type: str) -> str:
    t = (item_type or "").lower()

    # direct matches
    if t in {"event", "bts", "news", "recap", "merch", "film"}:
        return t

    # common aliases
    if t in {"youtube_upload", "youtube"}:
        return "film"
    if t in {"deadline", "callout_deadline", "submission_deadline"}:
        return "news"  # deadlines behave like news/announcements
    if t in {"update", "behind_the_scenes"}:
        return "bts"

    # fallback
    return "news"


def _calc_urgency(item, ref_dt):
    if not item.event_start:
        return 3.0

    event_dt = item.event_start
    if event_dt.tzinfo is None:
        event_dt = event_dt.replace(tzinfo=timezone.utc)
    if ref_dt.tzinfo is None:
        ref_dt = ref_dt.replace(tzinfo=timezone.utc)

    days_until = (event_dt.date() - ref_dt.date()).days

    if days_until < 0:
        return 0.0
    if days_until == 0:
        return 30.0
    if days_until <= 3:
        return 25.0
    if days_until <= 7:
        return 20.0
    if days_until <= 14:
        return 12.0
    if days_until <= 30:
        return 6.0
    return 2.0


def _get_platform_base_weight(cfg, platform):
    pw = cfg.get("platform_weights") or {}
    weights = pw.get("weights") or {}
    p = weights.get(platform) or {}
    try:
        return float(p.get("base_weight", 0))
    except (TypeError, ValueError):
        return 0.0
    
def _get_format_bias(cfg, platform, fmt):
    pw = cfg.get("platform_weights") or {}
    weights = pw.get("weights") or {}
    p = weights.get(platform) or {}
    biases = p.get("format_biases") or {}
    try:
        return float(biases.get(fmt, 0))
    except (TypeError, ValueError):
        return 0.0


def _get_content_fit(cfg, platform, item_type):
    sr = cfg.get("scoring_rules") or {}
    cf = sr.get("content_fit") or {}
    plat_map = cf.get(platform) or {}

    fit_key = _map_item_type_to_fit_key(item_type)

    try:
        return float(plat_map.get(fit_key, 0))
    except (TypeError, ValueError):
        return 0.0


def _score_candidate(item, platform, fmt, cfg, objectives, ref_dt):
    urgency = _calc_urgency(item, ref_dt)
    objective_weights = _parse_objective_weights(objectives)
    obj_key = _pick_primary_objective(item)
    obj_score = float(objective_weights.get(obj_key, 0.0)) if obj_key else 0.0

    platform_score = _get_platform_base_weight(cfg, platform)
    format_bias = _get_format_bias(cfg, platform, fmt)
    content_fit = _get_content_fit(cfg, platform, item.item_type)

    total = urgency + obj_score + platform_score + format_bias + content_fit

    breakdown = {
        "urgency": urgency,
        "objective": {"key": obj_key, "score": obj_score},
        "platform": platform_score,
        "format_bias": format_bias,
        "content_fit": content_fit,
        "total": total,
    }
    return total, breakdown


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

    # Coerce incoming dict items (API payload) into Item models
    coerced_items: list[Item] = []
    for it in items:
        if isinstance(it, Item):
            coerced_items.append(it)
        else:
            coerced_items.append(Item.model_validate(it))
    items = coerced_items

    campaigns = campaigns or []
    objectives = objectives or []
    configs = configs or {}

    planner_settings = configs.get("planner_settings_v1") or {}
    cooldowns = planner_settings.get("cooldowns") or {}
    push_windows = planner_settings.get("push_windows") or {}

    stored_approvals = get_all_approvals()

    formats_by_platform: dict[str, list[str]] = (
        ((configs.get("scoring_rules") or {}).get("candidate_generation") or {}).get("formats_by_platform") or {}
    )
    dependency_rules: list[dict[str, Any]] = ((configs.get("dependency_rules") or {}).get("rules") or [])

    draft_candidates: list[DraftCandidate] = []

    now_utc = datetime.utcnow()

    for item in items:
        for platform, formats in formats_by_platform.items():
            for fmt in formats:
                blocked, block_reason = _evaluate_dependencies(item, platform, fmt, dependency_rules)

                score, breakdown = _score_candidate(
                    item=item,
                    platform=platform,
                    fmt=fmt,
                    cfg=configs,
                    objectives=objectives,
                    ref_dt=now_utc,
                )

                draft_candidates.append(
                    DraftCandidate(
                        item_id=item.id,
                        platform=platform,
                        format=fmt,
                        blocked=blocked,
                        block_reason=block_reason,
                        score=score,
                        score_breakdown=breakdown,
                    )
                )

    # ======================
    # Milestone C: Baseline scheduling (Mondays only)
    # ======================

    weekly_plan: list[dict[str, Any]] = []

    horizon_days = 28
    horizon_end = now_utc + timedelta(days=horizon_days)

    mondays = _iter_mondays(now_utc, horizon_end)

    # Build a quick lookup of items by id for re-scoring
    item_by_id = {it.id: it for it in items}

    def _cooldown_days_for(it: Item, platform: str, slot_dt: datetime) -> int:
        # base cooldown
        base = int((cooldowns.get(platform) or 14))

        # ramp-up overrides for events near the date
        # only applies if item has event_start
        if it.event_start:
            days_until = (it.event_start.date() - slot_dt.date()).days

            level = (it.push_level or "normal").lower()
            windows = push_windows.get(level) or {}

            within_days = windows.get("within_days")
            override = windows.get("cooldown_days")

            if isinstance(within_days, int) and isinstance(override, int):
                if 0 <= days_until <= within_days:
                    return override

        return base
    
    last_scheduled: dict[tuple[str, str], datetime] = {}

    def pick_best_for_slot(platform: str, slot_dt: datetime) -> DraftCandidate | None:
        eligible: list[DraftCandidate] = []

        for c in draft_candidates:
            if c.platform != platform or c.blocked:
                continue

            draft_id = f"{c.item_id}:{c.platform}:{c.format}"
            if stored_approvals.get(draft_id) == "rejected":
                continue

            it = item_by_id.get(c.item_id)
            if not it:
                continue

            # cooldown key: series if present, else item
            key_id = it.series_id or it.id
            key = (key_id, platform)

            cd_days = _cooldown_days_for(it, platform, slot_dt)
            last = last_scheduled.get(key)
            if last and (slot_dt - last).days <= cd_days:
                continue

            eligible.append(c)

        if not eligible:
            return None

        # scoring pass using slot_dt as ref
        best: DraftCandidate | None = None
        best_score = float("-inf")
        best_breakdown: dict[str, Any] = {}

        for cand in eligible:
            it = item_by_id.get(cand.item_id)
            if not it:
                continue

            score, breakdown = _score_candidate(
                item=it,
                platform=cand.platform,
                fmt=cand.format,
                cfg=configs,
                objectives=objectives,
                ref_dt=slot_dt,
            )

            if score > best_score:
                best = cand
                best_score = score
                best_breakdown = breakdown

        if best:
            best.score = best_score
            best.score_breakdown = best_breakdown
            best.suggested_schedule_datetime = slot_dt.isoformat()

            # record last scheduled now that we’ve chosen it
            it = item_by_id.get(best.item_id)
            if it:
                key_id = it.series_id or it.id
                last_scheduled[(key_id, platform)] = slot_dt

        return best

    for monday in mondays:
        ig_dt = monday.replace(hour=18, minute=0)
        fb_dt = monday.replace(hour=19, minute=0)

        ig_best = pick_best_for_slot("instagram", ig_dt)
        if ig_best:
            weekly_plan.append(
                {
                    "draft_id": f"{ig_best.item_id}:instagram:{ig_best.format}",
                    "platform": "instagram",
                    "scheduled_datetime": ig_dt.isoformat(),
                }
            )

        fb_best = pick_best_for_slot("facebook", fb_dt)
        if fb_best:
            weekly_plan.append(
                {
                    "draft_id": f"{fb_best.item_id}:facebook:{fb_best.format}",
                    "platform": "facebook",
                    "scheduled_datetime": fb_dt.isoformat(),
                }
            )


        # ======================
    # Milestone D1: Approval queue (from weekly plan)
    # ======================

    approval_queue: list[dict[str, Any]] = []
    for entry in weekly_plan:
        draft_id = entry["draft_id"]
        item_id = draft_id.split(":", 1)[0]

        stored_status = stored_approvals.get(draft_id, "proposed")

        approval_queue.append(
            {
                "draft_id": draft_id,
                "item_id": item_id,
                "platform": entry["platform"],
                "scheduled_datetime": entry["scheduled_datetime"],
                "status": stored_status,
            }
        )

    approval_queue.sort(key=lambda e: e["scheduled_datetime"])
    
    blocked_count = sum(1 for c in draft_candidates if c.blocked)
    total_count = len(draft_candidates)

    return PlannerResult(
        draft_candidates=draft_candidates,
        weekly_plan=weekly_plan,
        approval_queue=approval_queue,
        export_queue=[],
        metadata={
            "status": "milestone_c",
            "message": "Candidate generation, dependency gating, scoring, and baseline Monday scheduling implemented.",
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
            "scheduled_slots": len(weekly_plan),
            "horizon_days": 28,
            "validation_status": "passed",
        },
    )