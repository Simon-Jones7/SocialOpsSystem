from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_FILES = [
    "cadence_policy_v1.yaml",
    "export_specs_v1.yaml",
    "export_mapping_v1.yaml",
    "platform_weights.yaml",
    "scoring_rules.yaml",
    "campaign_templates.yaml",
    "audience_schema.yaml",
    "dependency_rules.yaml",
    "planner_settings_v1.yaml",
]


@dataclass
class ConfigLoader:
    """Loads YAML config files into a single dict keyed by filename (without extension)."""

    config_dir: Path | None = None
    files: list[str] | None = None

    def load_all(self) -> dict[str, Any]:
        base = self.config_dir or Path(__file__).resolve().parents[2] / "configs"
        files = self.files or DEFAULT_CONFIG_FILES

        cfg: dict[str, Any] = {}
        for fname in files:
            path = base / fname
            if not path.exists():
                raise FileNotFoundError(f"Missing config file: {path}")
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            key = Path(fname).stem
            cfg[key] = data
        return cfg

