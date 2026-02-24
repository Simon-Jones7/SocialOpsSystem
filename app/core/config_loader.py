from pathlib import Path
from typing import Any

import yaml


CONFIG_FILES = [
    "planner_settings_v1.yaml",
    "cadence_policy_v1.yaml",
    "export_specs_v1.yaml",
    "export_mapping_v1.yaml",
    "platform_weights.yaml",
    "scoring_rules.yaml",
    "campaign_templates.yaml",
    "audience_schema.yaml",
    "dependency_rules.yaml",
]


class ConfigLoader:
    def __init__(self, config_dir: str = "config") -> None:
        self.config_dir = Path(config_dir)

    def load_all(self) -> dict[str, Any]:
        loaded: dict[str, Any] = {}
        for filename in CONFIG_FILES:
            file_path = self.config_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Missing config file: {file_path}")
            with file_path.open("r", encoding="utf-8") as f:
                loaded[filename] = yaml.safe_load(f) or {}
        return loaded
