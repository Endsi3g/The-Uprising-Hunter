from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")


REQUIRED_TOP_LEVEL_KEYS = (
    "icp_weights",
    "heat_weights",
    "thresholds",
    "tier_cutoffs",
    "caps",
    "rules",
)


REQUIRED_NUMERIC_PATHS = (
    ("thresholds", "qualification_min_score"),
    ("thresholds", "heat_hot_min"),
    ("thresholds", "heat_warm_min"),
    ("tier_cutoffs", "tier_a"),
    ("tier_cutoffs", "tier_b"),
    ("tier_cutoffs", "tier_c"),
    ("caps", "fit"),
    ("caps", "pain"),
    ("caps", "digital"),
    ("caps", "access_urgency"),
    ("caps", "email_engagement"),
    ("caps", "site_reply"),
    ("caps", "timing"),
    ("caps", "total_icp"),
    ("caps", "total_heat"),
    ("icp_weights", "fit", "prac_2_5"),
    ("icp_weights", "fit", "medical_industry"),
    ("icp_weights", "fit", "location_priority"),
    ("icp_weights", "fit", "admin_present"),
    ("icp_weights", "fit", "solo_penalty"),
    ("icp_weights", "fit", "group_10_penalty"),
    ("icp_weights", "pain", "high_friction"),
    ("icp_weights", "pain", "vague_booking"),
    ("icp_weights", "pain", "no_faq"),
    ("icp_weights", "pain", "missing_essentials"),
    ("icp_weights", "pain", "surcharge_signals"),
    ("icp_weights", "digital", "bad_mobile"),
    ("icp_weights", "digital", "no_fold_cta"),
    ("icp_weights", "digital", "weak_contact"),
    ("icp_weights", "access", "direct_email"),
    ("icp_weights", "urgency", "recent_post"),
    ("heat_weights", "email", "open"),
    ("heat_weights", "email", "click"),
    ("heat_weights", "email", "double_open"),
    ("heat_weights", "email", "forward"),
    ("heat_weights", "site", "pricing_page"),
    ("heat_weights", "site", "return_visit"),
    ("heat_weights", "reply", "curiosity"),
    ("heat_weights", "timing", "within_24h"),
    ("heat_weights", "timing", "within_48h"),
    ("heat_weights", "intent", "high"),
    ("heat_weights", "intent", "medium"),
    ("heat_weights", "intent", "low"),
)


def _get(config: dict[str, Any], path: Iterable[str]) -> Any:
    current: Any = config
    for key in path:
        if not isinstance(current, dict) or key not in current:
            dotted = ".".join(path)
            raise ValueError(f"Missing required scoring config key: {dotted}")
        current = current[key]
    return current


def _require_mapping(config: dict[str, Any], path: tuple[str, ...]) -> None:
    value = _get(config, path)
    if not isinstance(value, dict):
        dotted = ".".join(path)
        raise ValueError(f"Config key must be a mapping: {dotted}")


def _require_numeric(config: dict[str, Any], path: tuple[str, ...]) -> None:
    value = _get(config, path)
    if not isinstance(value, (int, float)):
        dotted = ".".join(path)
        raise ValueError(f"Config key must be numeric: {dotted}")


def validate_scoring_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("Scoring config must be a mapping.")

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in config:
            raise ValueError(f"Missing required scoring config section: {key}")

    _require_mapping(config, ("icp_weights",))
    _require_mapping(config, ("heat_weights",))
    _require_mapping(config, ("thresholds",))
    _require_mapping(config, ("tier_cutoffs",))
    _require_mapping(config, ("caps",))
    _require_mapping(config, ("rules",))
    _require_mapping(config, ("rules", "fit"))
    _require_mapping(config, ("rules", "pain"))
    _require_mapping(config, ("rules", "digital"))
    _require_mapping(config, ("rules", "urgency"))
    _require_mapping(config, ("rules", "timing"))
    _require_mapping(config, ("rules", "heat"))
    _require_mapping(config, ("rules", "actions"))
    _require_mapping(config, ("rules", "actions", "tier"))
    _require_mapping(config, ("rules", "actions", "heat"))

    for path in REQUIRED_NUMERIC_PATHS:
        _require_numeric(config, path)

    tier_a = _get(config, ("tier_cutoffs", "tier_a"))
    tier_b = _get(config, ("tier_cutoffs", "tier_b"))
    tier_c = _get(config, ("tier_cutoffs", "tier_c"))
    if not (tier_a >= tier_b >= tier_c):
        raise ValueError("tier_cutoffs must satisfy tier_a >= tier_b >= tier_c")

    heat_hot_min = _get(config, ("thresholds", "heat_hot_min"))
    heat_warm_min = _get(config, ("thresholds", "heat_warm_min"))
    if not (heat_hot_min >= heat_warm_min):
        raise ValueError("thresholds must satisfy heat_hot_min >= heat_warm_min")

    return config


def load_scoring_config(config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Scoring config not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        parsed = yaml.safe_load(handle) or {}

    return validate_scoring_config(parsed)
