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


class ConfigValidationError(ValueError):
    pass


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

        self._validate_cross_file_keys(loaded)
        return loaded

    def _validate_cross_file_keys(self, cfg: dict[str, Any]) -> None:
        cadence_platforms = set((cfg["cadence_policy_v1.yaml"].get("platform_caps") or {}).keys())
        weight_platforms = set((cfg["platform_weights.yaml"].get("weights") or {}).keys())
        scoring_platforms = set(
            (((cfg["scoring_rules.yaml"].get("candidate_generation") or {}).get("formats_by_platform") or {}).keys())
        )
        mapping_platforms = set((cfg["export_mapping_v1.yaml"].get("mapping") or {}).keys())

        platform_sources = {
            "cadence_policy.platform_caps": cadence_platforms,
            "platform_weights.weights": weight_platforms,
            "scoring_rules.candidate_generation.formats_by_platform": scoring_platforms,
            "export_mapping.mapping": mapping_platforms,
        }
        self._raise_if_platform_mismatch(platform_sources)

        scoring_formats = (cfg["scoring_rules.yaml"].get("candidate_generation") or {}).get("formats_by_platform") or {}
        weight_biases = cfg["platform_weights.yaml"].get("weights") or {}
        export_mapping = cfg["export_mapping_v1.yaml"].get("mapping") or {}
        export_specs = set((cfg["export_specs_v1.yaml"].get("specs") or {}).keys())

        format_errors: list[str] = []
        referenced_specs_all: set[str] = set()

        for platform in sorted(scoring_platforms):
            sf = set(scoring_formats.get(platform) or [])
            wb = set(((weight_biases.get(platform) or {}).get("format_biases") or {}).keys())
            em = set((export_mapping.get(platform) or {}).keys())

            if sf != wb:
                format_errors.append(
                    self._diff_message(
                        f"{platform}: scoring_rules.formats_by_platform vs platform_weights.format_biases",
                        sf,
                        wb,
                    )
                )

            if sf != em:
                format_errors.append(
                    self._diff_message(
                        f"{platform}: scoring_rules.formats_by_platform vs export_mapping.mapping",
                        sf,
                        em,
                    )
                )

            for fmt in sf:
                mapped_specs = (export_mapping.get(platform) or {}).get(fmt)
                if mapped_specs is not None:
                    referenced_specs_all.update(mapped_specs)

        missing_specs = sorted(referenced_specs_all - export_specs)
        extra_specs = sorted(export_specs - referenced_specs_all)
        if missing_specs or extra_specs:
            format_errors.append(
                "export_specs vs export_mapping referenced IDs: "
                f"missing={missing_specs} extra={extra_specs}"
            )

        if format_errors:
            raise ConfigValidationError("Format key validation failed:\n- " + "\n- ".join(format_errors))

    def _raise_if_platform_mismatch(self, sources: dict[str, set[str]]) -> None:
        if not sources:
            return

        baseline_name = next(iter(sources.keys()))
        baseline = sources[baseline_name]

        errors: list[str] = []
        for name, keys in sources.items():
            missing = sorted(baseline - keys)
            extra = sorted(keys - baseline)
            if missing or extra:
                errors.append(f"{name}: missing={missing} extra={extra} (baseline={baseline_name})")

        if errors:
            raise ConfigValidationError("Platform key validation failed:\n- " + "\n- ".join(errors))

    @staticmethod
    def _diff_message(label: str, left: set[str], right: set[str]) -> str:
        missing = sorted(left - right)
        extra = sorted(right - left)
        return f"{label}: missing={missing} extra={extra}"
