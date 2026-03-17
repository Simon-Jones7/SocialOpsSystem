# PVTV Social Ops System (Config + Backend Skeleton)

This repository contains:

- A **v1 configuration scaffold** for the planner engine (`configs/*.yaml`)
- A **backend skeleton** using FastAPI + Docker Compose

## Included config files

- `configs/planner_settings_v1.yaml` — global defaults (horizon, mode, thresholds, email spacing)
- `configs/cadence_policy_v1.yaml` — platform cadence, baseline slots, extra post triggers
- `configs/platform_weights.yaml` — base weights and per-format biases
- `configs/scoring_rules.yaml` — candidate generation formats and scoring components
- `configs/export_specs_v1.yaml` — export format specs by media output type
- `configs/export_mapping_v1.yaml` — maps platform+format to export specs
- `configs/campaign_templates.yaml` — phase templates and multipliers
- `configs/audience_schema.yaml` — audience affinity multipliers per platform
- `configs/dependency_rules.yaml` — gating rules and block messages

## Backend skeleton

### Services

`docker-compose.yml` defines:

- `api` (FastAPI)
- `postgres`
- `redis`
- `worker` (placeholder loop)

### API endpoints

- `GET /health` -> simple health status
- `POST /planner/run` -> loads YAML config and returns placeholder planner envelope

`run_planner()` currently returns an empty plan structure by design.
Scoring and scheduling logic is intentionally not implemented yet.

## Local run

```bash
docker compose up --build
```

Then open:

- http://localhost:8000/health
- http://localhost:8000/docs

## Next implementation step

Implement planner internals behind `run_planner()`:

1. Candidate generation (`Item × Platform × Format`)
2. Dependency gating
3. Two-pass scoring and scheduling
4. Approval/export queue population
