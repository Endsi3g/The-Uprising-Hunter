from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


SUPPORTED_LEVELS = {"none", "low", "medium", "high"}


def _to_level(value: Any) -> str:
    if value is None:
        return "none"
    level = str(value).strip().lower()

    synonyms = {
        "very-high": "high",
        "hot": "high",
        "warm": "medium",
        "cold": "low",
    }
    level = synonyms.get(level, level)
    if level not in SUPPORTED_LEVELS:
        return "none"
    return level


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_topics(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def normalize_intent_payload(
    provider: str,
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    provider_name = (provider or "unknown").lower()
    data = payload or {}

    if provider_name == "bombora":
        topics = _as_topics(data.get("topics"))
        surge_score = _safe_float(data.get("surge_score", data.get("intent_score", 0)))
        level = _to_level(data.get("intent_level"))
        if level == "none":
            if surge_score >= 75:
                level = "high"
            elif surge_score >= 45:
                level = "medium"
            elif surge_score > 0:
                level = "low"

        return {
            "provider": "bombora",
            "intent_level": level,
            "surge_score": surge_score,
            "topic_count": _safe_int(data.get("topic_count", len(topics))),
            "topics": topics,
            "confidence": _safe_float(data.get("confidence", 0.7)),
            "raw": data,
        }

    if provider_name in {"6sense", "sixsense"}:
        topics = _as_topics(data.get("topics", data.get("keywords")))
        score = _safe_float(data.get("intent_score", data.get("score", 0)))
        stage = str(data.get("buying_stage", "")).lower()
        level = _to_level(data.get("intent_level"))
        if level == "none":
            if "decision" in stage or score >= 80:
                level = "high"
            elif "consider" in stage or score >= 50:
                level = "medium"
            elif score > 0:
                level = "low"

        return {
            "provider": "6sense",
            "intent_level": level,
            "surge_score": score,
            "topic_count": _safe_int(data.get("topic_count", len(topics))),
            "topics": topics,
            "confidence": _safe_float(data.get("confidence", 0.7)),
            "buying_stage": stage or None,
            "raw": data,
        }

    # Fallback behavior for mock/unknown providers.
    topics = _as_topics(data.get("topics"))
    return {
        "provider": provider_name,
        "intent_level": _to_level(data.get("intent_level")),
        "surge_score": _safe_float(data.get("surge_score", 0)),
        "topic_count": _safe_int(data.get("topic_count", len(topics))),
        "topics": topics,
        "confidence": _safe_float(data.get("confidence", 0.5)),
        "raw": data,
    }

