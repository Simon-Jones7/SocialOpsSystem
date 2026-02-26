What exists now

YAML config loader merges configs in /configs.

Planner generates draft candidates from scoring_rules.yaml candidate_generation.formats_by_platform.

Dependency gating applies dependency_rules.yaml to block candidates.

Pass 1 scoring implemented:

urgency based on days until event_start

objective alignment via API payload objectives[] and item_type mapping

platform base weight + format bias from platform_weights.yaml (weights.<platform>.base_weight, format_biases)

content_fit from scoring_rules.yaml using mapped fit keys (eg youtube_upload -> film, deadlines -> news)

Baseline scheduling implemented:

Monday slots only (currently hard-coded 18:00 Instagram, 19:00 Facebook)

28 day horizon

Uses cooldowns per platform (from planner_settings_v1.yaml) with optional push window overrides by push_level near event dates

Rejected drafts excluded using approvals_store.get_all_approvals()

Approval queue generated from weekly plan:

includes stored status per draft_id (defaults to proposed)

sorted by scheduled time

Known limitations

Items never expire (“done” concept not implemented yet). Planned next: eligibility windows by item_type so one-off releases stop after event_start.

Scheduling is baseline-only and does not yet use extra slots or email cadence rules from planner settings.

Timezone handling is still mostly UTC in planner logic.

How to run

docker compose up --build

POST /planner/run with items payload to see draft_candidates, weekly_plan, approval_queue.
